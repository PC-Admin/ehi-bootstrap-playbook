# filter_plugins/to_letter.py
from ansible.errors import AnsibleFilterError

def int_to_letter(value):
    try:
        value = int(value)
        if value < 1 or value > 26:
            raise ValueError()
        return chr(value + 96)
    except (TypeError, ValueError):
        raise AnsibleFilterError(f"Invalid input for int_to_letter: {value}")

class FilterModule(object):
    def filters(self):
        return {
            'to_letter': int_to_letter
        }
