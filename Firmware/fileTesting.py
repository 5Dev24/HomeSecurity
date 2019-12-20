from src.file import File, FileSystem, FileFormat, AccessMode

testFile = File.getOrCreate(FileSystem, "test.dat")

print(testFile.obj(AccessMode.Read, File.read))

testFormat = FileFormat(0)
lines = []

i = input("Write: ")
while i != "":
	lines.append(i)
	i = input("Write: ")

testFormat.data = lines
testFormat.write(testFile)

print(testFile.obj(AccessMode.Read, File.read))

testFormat = testFormat.loadFrom(testFile)

print("Lines:")
for data in testFormat.data: print(data)
