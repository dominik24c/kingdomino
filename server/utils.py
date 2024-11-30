def list_to_str(numbers_list):
    return " ".join([str(n) for n in numbers_list])


def get_command_and_args_from_player(msg):
    messages = msg.rstrip("\n").split(" ")
    utilized_list = list(filter(lambda char: char != "", messages))

    return utilized_list[0], utilized_list[1:]
