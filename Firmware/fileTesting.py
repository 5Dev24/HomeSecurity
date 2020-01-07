from src.file import File, FileSystem, FileFormat, AccessMode

testFile = File.getOrCreate(FileSystem, "test.dat")

print(testFile.obj(AccessMode.Read, File.read))

testFormat = FileFormat(0)
lines = []

while True:
	i = input("Write: ")
	if i == "" or i == None:
		break
	lines.append(i)

testFormat.data = lines
testFormat.write(testFile)

print(testFile.obj(AccessMode.Read, File.read))

testFormat = testFormat.loadFrom(testFile)

print("Lines:")
for data in testFormat.data: print(data)
