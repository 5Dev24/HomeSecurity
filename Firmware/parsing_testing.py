from src import parsing as _parsing

def callback_fucntion(arg1_passed, arg2_passed):
	print("callback function has been called!")
	print("arg1 is", arg1_passed)
	print("arg2 is", arg2_passed)

arg1_base = _parsing.Variable("arg1", _parsing.Type.STRING)
arg2_base = _parsing.Variable("arg2", _parsing.Type.FLOAT)

cmd = _parsing.Command("Test", callback_fucntion, arg1_base, arg2_base)

arg1_val = _parsing.Value("test string")
arg2_val = _parsing.Value(10.0)

arg1_arg = _parsing.Argument("arg1", arg1_val)
arg2_arg = _parsing.Argument("arg2", arg2_val)

cmd.set_arguments([arg1_arg, arg2_arg])

print(cmd)

cmd.invoke()