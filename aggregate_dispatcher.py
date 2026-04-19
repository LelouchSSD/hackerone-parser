from collections import Counter


def dispatch(data):
    root_obj = data.get("data", {}) 
    if not root_obj:
        return {}

    if 'resource' in root_obj and isinstance(root_obj['resource'], dict):
        return {'profile': user_info(root_obj)}

    if 'search' in root_obj and isinstance(root_obj['search'], dict):
        return weaknesses(root_obj)

    user_obj = root_obj.get('user')
    if isinstance(user_obj, dict):
        result = {}
        
        if 'memberships' in user_obj:
            result['memberships'] = memberships_info(user_obj)
            
        if 'user_streak' in user_obj:
            result.update(user_stats(user_obj))

        if 'statistics_snapshot' in user_obj:
            result.update(snapshot(user_obj))

        return result

def user_info(data):
    resource = data.get('resource')
    return {
        'username': resource.get('username'),
        'id': resource.get('id'),
        'url': resource.get('url'),
    }

def memberships_info(data):
    memberships = data.get('memberships')
    return {
        'total_count': memberships.get('total_count'),
    }

def user_stats(data):
    location = data.get('location') or None
    website = data.get('website') or None
    bio = data.get('bio') or None

    handlers = {
        'bugcrowd': data.get('bugcrowd_handle'),
        'hack_the_box': data.get('hack_the_box_handle'),
        'github': data.get('github_handle'),
        'gitlab': data.get('gitlab_handle'),
        'linkedin': data.get('linkedin_handle'),
        'twitter': data.get('twitter_handle'),
    }
    clean_handlers = {k: v for k, v in handlers.items() if v}

    badges_data = data.get('badges') or {}
    badges_list = badges_data.get('edges') or []
    def extract_badge_info(badge):
        date = badge.get('awarded_at')
        date_short = date[:10] if date else None
        node = badge.get('node') or {}
        name = node.get('name')
        return [date_short, name]
    raw_badges = [extract_badge_info(b) for b in badges_list]
    unique_badges = list(dict.fromkeys(tuple(b) for b in raw_badges))

    return {
        'user_stats': {
            'resolved_report_count': data.get('resolved_report_count'),
            'thanks_items_total_count': data.get('thanks_items_total_count'),
            'registered_at': (data.get('created_at') or '')[:10] or None,
            'location': location,
            'website': website,
            'bio': bio,
            'handlers': clean_handlers,
            'badges': {
                'badges_count': len(unique_badges),
                'badges_names': [list(b) for b in unique_badges],
            },
        }
    }

def snapshot(data):
    snapshot_stats = data.get('statistics_snapshot')

    return {
        'snapshot': {
                'signal': snapshot_stats.get('signal') or None,
                'signal_percentile': snapshot_stats.get('signal_percentile') or None,
                'impact': snapshot_stats.get('impact') or None,
                'impact_percentile': snapshot_stats.get('impact_percentile') or None,
                'reputation': snapshot_stats.get('reputation') or None,
                'rank': snapshot_stats.get('rank') or None,
        }
    }

def weaknesses(data):
    wk_data = data.get('search') or {}
    nodes = wk_data.get('nodes') or []
    ids_list = [node.get('cwe') for node in nodes if node.get('cwe')]
    
    return {'weakness_stats': dict(Counter(ids_list))}
