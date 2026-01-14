#!/usr/bin/env python3
"""Phase plot - state space trajectory.

Author: Simão Eugénio
Date: 2025-12-30
"""
from .base_plot import BasePlot


class PhasePlot(BasePlot):
    """Phase plot showing trajectory in state space.
    
    Features:
    - 2D or 3D phase space
    - Trajectory with time coloring
    - Requires 2-3 objects
    """
    
    def _create_plot(self, data):
        """Create phase plot.
        
        Args:
            data: Filtered time and object data
        """
        obj_data = data['data']
        
        num_objects = len(self.selected_objects)
        
        if num_objects < 2 or num_objects > 3:
            # Show instruction message
            self.axes.text(
                0.5, 0.5,
                'Phase plot requires 2 or 3 objects\n\nSelect 2 objects for 2D or 3 objects for 3D',
                horizontalalignment='center',
                verticalalignment='center',
                transform=self.axes.transAxes,
                fontsize=12,
                color='gray'
            )
            self.axes.set_xticks([])
            self.axes.set_yticks([])
            return
        
        # Get data for objects
        obj_ids = [obj.id for obj in self.selected_objects]
        data_arrays = []
        
        for obj_id in obj_ids:
            if obj_id not in obj_data:
                return
            data_arrays.append(obj_data[obj_id]['values'])
        
        if not all(data_arrays):
            return
        
        # Ensure same length
        min_len = min(len(d) for d in data_arrays)
        data_arrays = [d[:min_len] for d in data_arrays]
        
        if num_objects == 2:
            # 2D phase plot
            self._create_2d_phase(data_arrays)
        else:
            # 3D phase plot
            self._create_3d_phase(data_arrays)
    
    def _create_2d_phase(self, data_arrays):
        """Create 2D phase plot.
        
        Args:
            data_arrays: List of 2 data arrays
        """
        x_values = data_arrays[0]
        y_values = data_arrays[1]
        
        # Plot trajectory with time coloring
        points = self.axes.scatter(
            x_values,
            y_values,
            c=range(len(x_values)),
            cmap='viridis',
            alpha=0.6,
            s=20,
            edgecolors='black',
            linewidth=0.5
        )
        
        # Add trajectory line
        self.axes.plot(
            x_values,
            y_values,
            color='gray',
            alpha=0.3,
            linewidth=1,
            zorder=0
        )
        
        # Mark start and end
        self.axes.plot(x_values[0], y_values[0], 'go', markersize=10, label='Start', zorder=5)
        self.axes.plot(x_values[-1], y_values[-1], 'ro', markersize=10, label='End', zorder=5)
        
        # Add colorbar (only if points scatter was successful)
        if points:
            try:
                cbar = self.figure.colorbar(points, ax=self.axes)
                cbar.set_label('Time index', rotation=270, labelpad=15)
            except:
                pass  # Colorbar creation failed, skip it
        
        # Configure axes
        self.axes.set_xlabel(self.selected_objects[0].name, fontsize=12)
        self.axes.set_ylabel(self.selected_objects[1].name, fontsize=12)
        self.axes.set_title('Phase Space Trajectory (2D)', fontsize=14, fontweight='bold')
        self.axes.grid(True, alpha=0.3, linestyle='-')
        if self.show_legend:
            self.axes.legend(loc='best', framealpha=0.9)
        
        # Tight layout
        try:
            self.figure.tight_layout()
        except:
            pass  # tight_layout can fail with colorbar, skip if it does
    
    def _create_3d_phase(self, data_arrays):
        """Create 3D phase plot.
        
        Args:
            data_arrays: List of 3 data arrays
        """
        # Check if we need to recreate axes with 3D projection
        from mpl_toolkits.mplot3d import Axes3D
        if not isinstance(self.axes, Axes3D):
            # Clear all axes including colorbars
            for ax in self.figure.get_axes():
                ax.clear()
            # Recreate with 3D projection
            self.figure.clear()
            self.axes = self.figure.add_subplot(111, projection='3d')
        
        x_values = data_arrays[0]
        y_values = data_arrays[1]
        z_values = data_arrays[2]
        
        # Plot trajectory with time coloring
        points = self.axes.scatter(
            x_values,
            y_values,
            z_values,
            c=range(len(x_values)),
            cmap='viridis',
            alpha=0.6,
            s=20,
            edgecolors='black',
            linewidth=0.5
        )
        
        # Add trajectory line
        self.axes.plot(
            x_values,
            y_values,
            z_values,
            color='gray',
            alpha=0.3,
            linewidth=1
        )
        
        # Mark start and end
        self.axes.scatter([x_values[0]], [y_values[0]], [z_values[0]], 
                         color='green', s=100, label='Start')
        self.axes.scatter([x_values[-1]], [y_values[-1]], [z_values[-1]], 
                         color='red', s=100, label='End')
        
        # Add colorbar (only if points scatter was successful)
        if points:
            try:
                cbar = self.figure.colorbar(points, ax=self.axes, shrink=0.5)
                cbar.set_label('Time index', rotation=270, labelpad=15)
            except:
                pass  # Colorbar creation failed, skip it
        
        # Configure axes
        self.axes.set_xlabel(self.selected_objects[0].name, fontsize=10)
        self.axes.set_ylabel(self.selected_objects[1].name, fontsize=10)
        self.axes.set_zlabel(self.selected_objects[2].name, fontsize=10)
        self.axes.set_title('Phase Space Trajectory (3D)', fontsize=14, fontweight='bold')
        if self.show_legend:
            self.axes.legend(loc='best', framealpha=0.9)
        
        # Tight layout
        try:
            self.figure.tight_layout()
        except:
            pass  # tight_layout can fail with colorbar, skip if it does
    
    def _get_plot_title(self) -> str:
        """Get plot title.
        
        Returns:
            str: Plot title
        """
        return 'Phase Space Trajectory'
