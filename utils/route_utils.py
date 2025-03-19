from utils.command_utils import run_command

def create_route(vpn_ip, dev, table):
    route_cmd = [
        'sudo', 'ip', 'route', 'add', 'default',
        'via', vpn_ip,
        'dev', dev,
        'table', str(table)
    ]

    run_command(route_cmd)

def create_rule(vpn_ip, table):
    rule_cmd = [
        'sudo', 'ip', 'rule', 'add',
        'from', vpn_ip,
        'lookup', str(table)
    ]

    run_command(rule_cmd)

def delete_route(vpn_ip, dev, table):
    route_cmd = [
        'sudo', 'ip', 'route', 'del', 'default',
        'via', vpn_ip,
        'dev', dev,
        'table', str(table)
    ]
    run_command(route_cmd)

def delete_rule(vpn_ip, table):
    rule_cmd = [
        'sudo', 'ip', 'rule', 'del',
        'from', vpn_ip,
        'lookup', str(table)
    ]
    run_command(rule_cmd)