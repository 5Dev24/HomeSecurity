from src import arguments as _arguments

def default_command():
	print("default command was called!")

def callback_fucntion(arg1_passed, arg2_passed):
	print("callback function has been called!")
	print("arg1 is", arg1_passed)
	print("arg2 is", arg2_passed)

handler = _arguments.Handler()

default_cmd = _arguments.Command("default", default_command)

handler.set_default_command(default_cmd)

arg1_base = _arguments.BaseArgument("arg1", _arguments.Type.STRING)
arg2_base = _arguments.BaseArgument("arg2", _arguments.Type.NUMBER)

cmd = _arguments.Command("Test", callback_fucntion, arg1_base, arg2_base)

handler.add_command(cmd)

data = [
	"--test",
	"-arg1",
	'"hello',
	"my",
	"name",
	"is",
	'carl"',
	"-arg2",
	"72"
]

print("Lex code:", handler.lex(data))

print("Parse code:", handler.parse())