"""Base transition property dialog with type-specific behavior.

Provides context-sensitive UI that adapts based on transition type:
- Immediate: Priority, firing policy (no rate)
- Timed: Rate, firing policy, expressions
- Stochastic: Rate (λ), distribution type
- Continuous: ODE functions, rate expressions
"""

from typing import List, Dict, Optional, Any
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

from ..base import PropertyDialogBase, ExpressionValidator


class TransitionPropertyDialog(PropertyDialogBase):
    """Property dialog for transitions with type-specific field handling.
    
    Adapts UI based on transition type selected by user.
    Provides expression validation and field synchronization.
    """
    
    # Field visibility map by transition type
    FIELD_VISIBILITY = {
        'immediate': {
            'rate_entry': False,
            'rate_textview': False,
            'rate_section': False,
            'firing_policy_combo': True,
            'firing_policy_box': True,
        },
        'timed': {
            'rate_entry': True,
            'rate_textview': True,
            'rate_section': True,
            'firing_policy_combo': True,
            'firing_policy_box': True,
        },
        'stochastic': {
            'rate_entry': True,
            'rate_textview': True,
            'rate_section': True,
            'firing_policy_combo': False,
            'firing_policy_box': False,
        },
        'continuous': {
            'rate_entry': True,
            'rate_textview': True,
            'rate_section': True,
            'firing_policy_combo': False,
            'firing_policy_box': False,
        }
    }
    
    # Type descriptions for help text
    TYPE_DESCRIPTIONS = {
        'immediate': (
            "Immediate Transition\n"
            "• Fires instantly when enabled (zero delay)\n"
            "• Uses priority to resolve conflicts\n"
            "• Firing policy determines when to fire"
        ),
        'timed': (
            "Timed Transition\n"
            "• Deterministic delay before firing\n"
            "• Rate = delay duration\n"
            "• Can use expressions for dynamic rates"
        ),
        'stochastic': (
            "Stochastic Transition\n"
            "• Exponential distribution (default)\n"
            "• Rate = λ parameter (mean 1/λ)\n"
            "• Race conditions resolved randomly"
        ),
        'continuous': (
            "Continuous Transition\n"
            "• ODE-based continuous flow\n"
            "• Rate function defines flow rate\n"
            "• No discrete firing events"
        )
    }
    
    def __init__(self, *args, **kwargs):
        """Initialize transition property dialog."""
        # Current transition type (updated when combo changes)
        self._current_type = None
        
        super().__init__(*args, **kwargs)
        
        # Connect type change handler after UI is loaded
        self._connect_type_change_handler()
        
        # Connect expression synchronization
        self._setup_expression_sync()
    
    # ========== PropertyDialogBase Implementation ==========
    
    def get_ui_filename(self) -> str:
        """Get UI filename."""
        return 'transition_prop_dialog.ui'
    
    def get_dialog_id(self) -> str:
        """Get dialog ID."""
        return 'transition_properties_dialog'
    
    def get_color_attribute_name(self) -> str:
        """Transitions use border_color."""
        return 'border_color'
    
    def get_color_picker_container_id(self) -> str:
        """Color picker container ID."""
        return 'transition_color_picker'
    
    def populate_fields(self):
        """Populate dialog fields with transition properties."""
        # Name (read-only system identifier)
        if hasattr(self.net_object, 'name'):
            self.set_entry_text('name_entry', self.net_object.name)
            name_entry = self.get_widget('name_entry')
            if name_entry:
                name_entry.set_editable(False)
        
        # Label (optional user text)
        if hasattr(self.net_object, 'label'):
            label = self.net_object.label or ''
            self.set_entry_text('transition_label_entry', label)
        
        # Transition type
        if hasattr(self.net_object, 'transition_type'):
            type_combo = self.get_widget('prop_transition_type_combo')
            if type_combo:
                transition_type = self.net_object.transition_type or 'continuous'
                type_map = {'immediate': 0, 'timed': 1, 'stochastic': 2, 'continuous': 3}
                index = type_map.get(transition_type, 3)
                type_combo.set_active(index)
                self._current_type = transition_type
        
        # Priority
        if hasattr(self.net_object, 'priority'):
            priority_spin = self.get_widget('priority_spin')
            if priority_spin:
                priority_spin.set_value(float(self.net_object.priority))
        
        # Firing policy
        if hasattr(self.net_object, 'firing_policy'):
            firing_policy_combo = self.get_widget('firing_policy_combo')
            if firing_policy_combo:
                policy_map = {'earliest': 0, 'latest': 1}
                policy = self.net_object.firing_policy or 'earliest'
                index = policy_map.get(policy, 0)
                firing_policy_combo.set_active(index)
        
        # Source/Sink checkboxes
        if hasattr(self.net_object, 'is_source'):
            is_source_check = self.get_widget('is_source_check')
            if is_source_check:
                is_source_check.set_active(self.net_object.is_source)
        
        if hasattr(self.net_object, 'is_sink'):
            is_sink_check = self.get_widget('is_sink_check')
            if is_sink_check:
                is_sink_check.set_active(self.net_object.is_sink)
        
        # Rate (basic entry)
        if hasattr(self.net_object, 'rate'):
            rate_value = self.net_object.rate
            
            # For continuous, try rate_function from properties first
            if self.net_object.transition_type == 'continuous':
                if hasattr(self.net_object, 'properties') and self.net_object.properties:
                    rate_func = self.net_object.properties.get('rate_function')
                    if rate_func is not None:
                        rate_value = rate_func
            
            rate_text = ExpressionValidator.format_for_display(rate_value)
            self.set_entry_text('rate_entry', rate_text)
        
        # Guard function (TextView)
        if hasattr(self.net_object, 'guard'):
            guard_value = self.net_object.guard
            
            # Try guard_function from properties first
            if hasattr(self.net_object, 'properties') and self.net_object.properties:
                guard_func = self.net_object.properties.get('guard_function')
                if guard_func is not None:
                    guard_value = guard_func
            
            guard_text = ExpressionValidator.format_for_display(guard_value)
            self.set_textview_text('guard_textview', guard_text)
        
        # Rate function (TextView)
        if hasattr(self.net_object, 'rate'):
            rate_value = self.net_object.rate
            
            # For continuous, prioritize properties['rate_function']
            if self.net_object.transition_type == 'continuous':
                if hasattr(self.net_object, 'properties') and self.net_object.properties:
                    rate_func = self.net_object.properties.get('rate_function')
                    if rate_func is not None:
                        rate_value = rate_func
            
            rate_text = ExpressionValidator.format_for_display(rate_value)
            self.set_textview_text('rate_textview', rate_text)
        
        # Update field visibility based on current type
        self._update_field_visibility(self._current_type or 'continuous')
    
    def validate_fields(self) -> List[str]:
        """Validate all fields and return errors."""
        errors = []
        
        # Get current transition type
        type_combo = self.get_widget('prop_transition_type_combo')
        if type_combo:
            type_map = {0: 'immediate', 1: 'timed', 2: 'stochastic', 3: 'continuous'}
            transition_type = type_map.get(type_combo.get_active(), 'continuous')
        else:
            transition_type = 'continuous'
        
        # Validate rate expression (if applicable for this type)
        if transition_type != 'immediate':
            rate_text = self.get_text_from_textview('rate_textview')
            if rate_text:
                is_valid, error_msg, _ = ExpressionValidator.validate_expression(
                    rate_text, allow_dict=False
                )
                if not is_valid:
                    errors.append(f"Rate function: {error_msg}")
        
        # Validate guard expression
        guard_text = self.get_text_from_textview('guard_textview')
        if guard_text:
            is_valid, error_msg, _ = ExpressionValidator.validate_expression(
                guard_text, allow_dict=True
            )
            if not is_valid:
                errors.append(f"Guard function: {error_msg}")
        
        # Type-specific validations
        if transition_type == 'immediate':
            # Immediate transitions shouldn't have rate in basic entry
            rate_entry_text = self.get_text_from_entry('rate_entry')
            if rate_entry_text and rate_entry_text not in ['', '0', '0.0']:
                errors.append(
                    "Immediate transitions fire instantly and don't use rate parameter"
                )
        
        return errors
    
    def apply_changes(self):
        """Apply validated changes to transition object."""
        # Store original values for rollback
        self.store_original_value('label')
        self.store_original_value('transition_type')
        self.store_original_value('rate')
        self.store_original_value('guard')
        self.store_original_value('priority')
        self.store_original_value('firing_policy')
        self.store_original_value('is_source')
        self.store_original_value('is_sink')
        self.store_original_value('border_color')
        
        # Store properties dict
        if hasattr(self.net_object, 'properties'):
            if self.net_object.properties is None:
                self.net_object.properties = {}
            self.store_original_value('properties')
        
        # Apply label
        label_text = self.get_text_from_entry('transition_label_entry')
        self.net_object.label = label_text
        
        # Apply transition type
        type_combo = self.get_widget('prop_transition_type_combo')
        if type_combo:
            type_map = {0: 'immediate', 1: 'timed', 2: 'stochastic', 3: 'continuous'}
            self.net_object.transition_type = type_map.get(type_combo.get_active(), 'continuous')
        
        # Apply priority
        priority_spin = self.get_widget('priority_spin')
        if priority_spin:
            self.net_object.priority = int(priority_spin.get_value())
        
        # Apply firing policy
        firing_policy_combo = self.get_widget('firing_policy_combo')
        if firing_policy_combo:
            policy_map = {0: 'earliest', 1: 'latest'}
            self.net_object.firing_policy = policy_map.get(firing_policy_combo.get_active(), 'earliest')
        
        # Apply source/sink
        is_source_check = self.get_widget('is_source_check')
        if is_source_check:
            self.net_object.is_source = is_source_check.get_active()
        
        is_sink_check = self.get_widget('is_sink_check')
        if is_sink_check:
            self.net_object.is_sink = is_sink_check.get_active()
        
        # Apply rate (use rate function if provided, otherwise basic entry)
        rate_func_text = self.get_text_from_textview('rate_textview')
        if rate_func_text:
            # Parse and store rate function
            is_valid, _, parsed = ExpressionValidator.validate_expression(
                rate_func_text, allow_dict=False
            )
            if is_valid:
                # Store in properties for later evaluation
                self.net_object.properties['rate_function'] = rate_func_text
                
                # Also store in rate attribute (as numeric if possible)
                if isinstance(parsed, (int, float)):
                    self.net_object.rate = float(parsed)
                else:
                    # Store expression string
                    self.net_object.rate = rate_func_text
        else:
            # Use basic rate entry
            rate_text = self.get_text_from_entry('rate_entry')
            if rate_text:
                try:
                    self.net_object.rate = float(rate_text)
                except ValueError:
                    self.net_object.rate = 1.0  # Default
            else:
                self.net_object.rate = 1.0
        
        # Apply guard
        guard_text = self.get_text_from_textview('guard_textview')
        if guard_text:
            is_valid, _, parsed = ExpressionValidator.validate_expression(
                guard_text, allow_dict=True
            )
            if is_valid:
                self.net_object.properties['guard_function'] = guard_text
                self.net_object.guard = parsed
        else:
            self.net_object.guard = None
            if 'guard_function' in self.net_object.properties:
                del self.net_object.properties['guard_function']
        
        # Apply color
        if self.color_picker:
            selected_color = self.color_picker.get_selected_color()
            if selected_color:
                self.net_object.border_color = selected_color
    
    # ========== Type-Specific Behavior ==========
    
    def _connect_type_change_handler(self):
        """Connect handler for transition type combo changes."""
        type_combo = self.get_widget('prop_transition_type_combo')
        if type_combo:
            type_combo.connect('changed', self._on_type_changed)
    
    def _on_type_changed(self, combo: Gtk.ComboBox):
        """Handle transition type selection change.
        
        Args:
            combo: The type combo box
        """
        type_map = {0: 'immediate', 1: 'timed', 2: 'stochastic', 3: 'continuous'}
        selected_type = type_map.get(combo.get_active(), 'continuous')
        
        self._current_type = selected_type
        
        # Update field visibility
        self._update_field_visibility(selected_type)
        
        # Update description text
        self._update_type_description(selected_type)
    
    def _update_field_visibility(self, transition_type: str):
        """Update field visibility based on transition type.
        
        Args:
            transition_type: Type string ('immediate', 'timed', etc.)
        """
        visibility_map = self.FIELD_VISIBILITY.get(transition_type, {})
        
        for widget_id, should_be_visible in visibility_map.items():
            widget = self.get_widget(widget_id)
            if widget:
                # Enable/disable instead of show/hide to preserve values
                widget.set_sensitive(should_be_visible)
                
                # Optional: Also hide disabled widgets
                # parent = widget.get_parent()
                # if parent:
                #     parent.set_visible(should_be_visible)
    
    def _update_type_description(self, transition_type: str):
        """Update description label with type-specific help text.
        
        Args:
            transition_type: Type string ('immediate', 'timed', etc.)
        """
        description_label = self.get_widget('type_description_label')
        if description_label:
            description = self.TYPE_DESCRIPTIONS.get(
                transition_type,
                "Select transition type for appropriate fields"
            )
            description_label.set_text(description)
    
    # ========== Expression Synchronization ==========
    
    def _setup_expression_sync(self):
        """Setup synchronization between advanced and basic fields."""
        # Rate function → Rate entry sync
        rate_textview = self.get_widget('rate_textview')
        rate_entry = self.get_widget('rate_entry')
        
        if rate_textview and rate_entry:
            buffer = rate_textview.get_buffer()
            buffer.connect('changed', self._on_rate_function_changed, rate_entry)
    
    def _on_rate_function_changed(self, buffer: Gtk.TextBuffer, rate_entry: Gtk.Entry):
        """Sync rate function TextView to basic rate Entry.
        
        Args:
            buffer: The TextBuffer that changed
            rate_entry: The Entry widget to update
        """
        # Get text from buffer
        start, end = buffer.get_bounds()
        expr_text = buffer.get_text(start, end, True).strip()
        
        if not expr_text:
            rate_entry.set_text("")
            rate_entry.set_tooltip_text("")
            return
        
        # Validate expression
        is_valid, error_msg, parsed = ExpressionValidator.validate_expression(
            expr_text, allow_dict=False
        )
        
        if not is_valid:
            # Show error
            rate_entry.set_text("[Invalid]")
            rate_entry.set_tooltip_text(error_msg)
            return
        
        # Update basic field
        if parsed is None:
            rate_entry.set_text("")
        elif isinstance(parsed, (int, float)):
            rate_entry.set_text(str(parsed))
        else:
            # It's an expression - show preview
            sample_state = self._get_sample_state()
            preview = ExpressionValidator.evaluate_preview(parsed, sample_state)
            rate_entry.set_text(f"[Expression] {preview}")
        
        rate_entry.set_tooltip_text("Synchronized from Rate Function")
    
    def _get_sample_state(self) -> Dict[str, Any]:
        """Get sample state for expression preview.
        
        Returns:
            Dictionary of place names to token counts
        """
        if not self.model:
            # Default sample state
            return {'P1': 10, 'P2': 5, 'P3': 2}
        
        # Get actual current marking
        marking = {}
        for place in self.model.places:
            marking[place.name] = place.tokens
        
        return marking if marking else {'P1': 10, 'P2': 5}
