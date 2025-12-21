from flask import Blueprint
from controllers.admin_controller import (
    # Helper functions
    check_admin_access,
    
    # Test endpoint
    test_admin_endpoint,
    
    # Dashboard endpoints
    get_dashboard_stats,
    get_sensor_history,
    get_quick_stats,
    
    # Messages endpoints
    get_admin_messages,
    mark_message_read,
    delete_message,
    admin_unread_count,
    get_thread_messages,
    
    # Message replies
    get_message_replies,
    send_message_reply,
    get_simple_replies,
    get_all_threads,
    
    # User management
    get_users,
    get_user_details,
    update_user,
    delete_user,
    create_user
)

# Create blueprint
admin_bp = Blueprint('admin', __name__, url_prefix='/api/admin')

# ========== TEST ENDPOINT ==========
admin_bp.route('/test', methods=['GET'])(test_admin_endpoint)

# ========== DASHBOARD ENDPOINTS ==========
admin_bp.route('/dashboard/stats', methods=['GET'])(get_dashboard_stats)
admin_bp.route('/dashboard/sensor-history', methods=['GET'])(get_sensor_history)
admin_bp.route('/dashboard/quick-stats', methods=['GET'])(get_quick_stats)

# ========== MESSAGES ENDPOINTS ==========
admin_bp.route('/messages', methods=['GET'])(get_admin_messages)
admin_bp.route('/messages/<int:message_id>/read', methods=['POST'])(mark_message_read)
admin_bp.route('/messages/<int:message_id>', methods=['DELETE'])(delete_message)
admin_bp.route('/messages/unread-count', methods=['GET'])(admin_unread_count)

# ========== MESSAGE REPLIES ENDPOINTS ==========
admin_bp.route('/messages/<int:message_id>/replies', methods=['GET'])(get_message_replies)
admin_bp.route('/messages/<int:message_id>/reply', methods=['POST'])(send_message_reply)
admin_bp.route('/messages/<int:message_id>/simple-replies', methods=['GET'])(get_simple_replies)
admin_bp.route('/messages/threads', methods=['GET'])(get_all_threads)
admin_bp.route('/messages/thread', methods=['GET'])(get_thread_messages)

admin_bp.route('/users', methods=['GET'])(get_users)
admin_bp.route('/users/<int:user_id>', methods=['GET'])(get_user_details)
admin_bp.route('/users/<int:user_id>', methods=['PUT'])(update_user)
admin_bp.route('/users/<int:user_id>', methods=['DELETE'])(delete_user)
admin_bp.route('/users', methods=['POST'])(create_user)