"""Parallel state-space exploration using basic work-stealing.

This module implements Phase 1: multiprocessing-based parallel exploration
with work-stealing load balancing. Workers atomically claim states and
explore them concurrently.
"""

from typing import Any, Dict, List
import multiprocessing
import queue
import time

from .base_explorer import StateSpaceExplorer


class ParallelBasicExplorer(StateSpaceExplorer):
    """Parallel exploration with work-stealing (Phase 1)."""
    
    def __init__(self, analyzer: Any, num_workers: int = None):
        """Initialize parallel explorer.
        
        Args:
            analyzer: Parent ReachabilityAnalyzer instance
            num_workers: Number of worker processes (default: CPU count)
        """
        super().__init__(analyzer)
        self.num_workers = num_workers or multiprocessing.cpu_count()
        
        # Cap workers to reasonable range
        if self.num_workers < 1:
            self.num_workers = 1
        elif self.num_workers > 32:
            self.num_workers = 32
    
    def explore(
        self,
        initial_marking: Dict[str, int],
        max_states: int,
        max_depth: int,
        compute_graph: bool,
        find_deadlocks: bool
    ) -> Dict[str, Any]:
        """Explore state space using parallel workers."""
        
        # ====================================================================
        # SHARED STATE INITIALIZATION
        # ====================================================================
        manager = multiprocessing.Manager()
        
        visited = manager.dict()  # {marking_tuple: state_id}
        visited_lock = manager.Lock()
        work_queue = manager.Queue()
        result_queue = manager.Queue()
        shutdown_event = manager.Event()  # Signal workers to stop
        
        stats = manager.dict({
            'states_explored': 0,
            'transitions_fired': 0,
            'max_depth': 0,
            'workers_active': 0,
            'work_in_progress': 0,  # Track states currently being processed
            'work_steals': 0,
            'next_state_id': 1  # State 0 is initial
        })
        
        # Add initial marking
        marking_tuple = self._marking_to_tuple(initial_marking)
        visited[marking_tuple] = 0
        work_queue.put((initial_marking, 0, 0))  # (marking, depth, state_id)
        
        # Report initial state
        if compute_graph:
            result_queue.put({
                'type': 'new_state',
                'state_id': 0,
                'marking': initial_marking,
                'depth': 0
            })
        
        # Check if initial state is deadlock
        if find_deadlocks:
            enabled = self._get_enabled_transitions(initial_marking)
            if not enabled:
                result_queue.put({
                    'type': 'deadlock',
                    'state_id': 0,
                    'marking': initial_marking
                })
        
        # ====================================================================
        # SPAWN WORKERS
        # ====================================================================
        workers = []
        for worker_id in range(self.num_workers):
            worker = multiprocessing.Process(
                target=self._worker_loop,
                args=(
                    worker_id,
                    work_queue,
                    result_queue,
                    visited_lock,
                    visited,
                    stats,
                    max_states,
                    max_depth,
                    find_deadlocks,
                    shutdown_event
                )
            )
            worker.start()
            workers.append(worker)
        
        # Wait for all workers to start (with timeout)
        import time
        start_wait = time.time()
        while stats['workers_active'] < self.num_workers and time.time() - start_wait < 5.0:
            time.sleep(0.01)
        
        # ====================================================================
        # COLLECT RESULTS
        # ====================================================================
        graph = {'nodes': [], 'edges': []} if compute_graph else None
        deadlock_states = []
        
        # Keep collecting while workers are active
        # Workers will exit on their own when exploration is complete
        while stats['workers_active'] > 0 or not result_queue.empty():
            try:
                result = result_queue.get(timeout=0.1)
                
                if result['type'] == 'new_state' and compute_graph:
                    graph['nodes'].append({
                        'id': result['state_id'],
                        'marking': result['marking'],
                        'depth': result['depth']
                    })
                
                elif result['type'] == 'transition' and compute_graph:
                    graph['edges'].append({
                        'source': result['source_id'],
                        'target': result['target_id'],
                        'transition': result['trans_id'],
                        'transition_name': self.analyzer._get_transition_name(result['trans_id'])
                    })
                
                elif result['type'] == 'deadlock' and find_deadlocks:
                    deadlock_states.append({
                        'state_id': result['state_id'],
                        'marking': result['marking']
                    })
            
            except queue.Empty:
                continue
        
        # Signal workers to shut down
        shutdown_event.set()
        
        # Wait for workers to finish
        for worker in workers:
            worker.join(timeout=5.0)
            if worker.is_alive():
                worker.terminate()
        
        # Drain any remaining items in queue
        while not result_queue.empty():
            try:
                result = result_queue.get(timeout=0.1)
                
                if result['type'] == 'new_state' and compute_graph:
                    graph['nodes'].append({
                        'id': result['state_id'],
                        'marking': result['marking'],
                        'depth': result['depth']
                    })
                
                elif result['type'] == 'transition' and compute_graph:
                    graph['edges'].append({
                        'source': result['source_id'],
                        'target': result['target_id'],
                        'transition': result['trans_id'],
                        'transition_name': self.analyzer._get_transition_name(result['trans_id'])
                    })
                
                elif result['type'] == 'deadlock' and find_deadlocks:
                    deadlock_states.append({
                        'state_id': result['state_id'],
                        'marking': result['marking']
                    })
            except queue.Empty:
                break
        
        # ====================================================================
        # CLEANUP
        # ====================================================================
        for worker in workers:
            if worker.is_alive():
                worker.terminate()
        
        return {
            'total_states': len(visited),
            'total_transitions': stats['transitions_fired'],
            'max_depth': stats['max_depth'],
            'states': None,  # Not tracked in parallel mode
            'graph': graph,
            'deadlock_states': deadlock_states,
            'exploration_stats': {
                'strategy': 'parallel_basic',
                'mode': 'work_stealing',
                'num_workers': self.num_workers,
                'work_steals': stats['work_steals']
            }
        }
    
    def _worker_loop(
        self,
        worker_id: int,
        work_queue: Any,
        result_queue: Any,
        visited_lock: Any,
        visited: Any,
        stats: Any,
        max_states: int,
        max_depth: int,
        find_deadlocks: bool,
        shutdown_event: Any
    ):
        """Worker process main loop."""
        stats['workers_active'] += 1
        
        try:
            consecutive_empty = 0
            max_consecutive_empty = 10  # 5 seconds of empty queue
            
            while not shutdown_event.is_set() and stats['next_state_id'] < max_states:
                try:
                    current_marking, depth, state_id = work_queue.get(timeout=0.5)
                    consecutive_empty = 0  # Reset on successful get
                    stats['work_in_progress'] += 1  # Mark state as being processed
                    
                    # Check depth limit
                    if depth >= max_depth:
                        stats['work_in_progress'] -= 1  # Decrement before continue
                        continue
                    
                    # Find enabled transitions
                    enabled = self._get_enabled_transitions(current_marking)
                    
                    # Check for deadlock
                    if not enabled and find_deadlocks:
                        result_queue.put({
                            'type': 'deadlock',
                            'state_id': state_id,
                            'marking': current_marking
                        })
                        stats['work_in_progress'] -= 1  # Decrement before continue
                        continue
                    
                    # Fire each enabled transition
                    for trans_id in enabled:
                        new_marking = self._fire_transition(current_marking, trans_id)
                        marking_tuple = self._marking_to_tuple(new_marking)
                        
                        # Atomic check-and-set
                        with visited_lock:
                            if marking_tuple not in visited:
                                new_state_id = stats['next_state_id']
                                stats['next_state_id'] = new_state_id + 1
                                visited[marking_tuple] = new_state_id
                                is_new_state = True
                                actual_state_id = new_state_id
                            else:
                                is_new_state = False
                                actual_state_id = visited[marking_tuple]
                        
                        # Report results outside lock
                        if is_new_state:
                            stats['max_depth'] = max(stats['max_depth'], depth + 1)
                            
                            result_queue.put({
                                'type': 'new_state',
                                'state_id': actual_state_id,
                                'marking': new_marking,
                                'depth': depth + 1
                            })
                            
                            work_queue.put((new_marking, depth + 1, actual_state_id))
                        
                        # Record transition
                        result_queue.put({
                            'type': 'transition',
                            'source_id': state_id,
                            'target_id': actual_state_id,
                            'trans_id': trans_id
                        })
                        
                        stats['transitions_fired'] += 1
                    
                    # Mark this state as fully processed
                    stats['work_in_progress'] -= 1
                
                except queue.Empty:
                    consecutive_empty += 1
                    if consecutive_empty >= max_consecutive_empty:
                        break  # Queue empty for 5 seconds - done
                    continue
        
        finally:
            stats['workers_active'] -= 1
