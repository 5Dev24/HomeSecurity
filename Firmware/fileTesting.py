from src.file import File, FileSystem, FileFormat, AccessMode

testFile = File.getOrCreate(FileSystem, "test.dat")

print("Before:")
print(testFile.obj(AccessMode.Read, File.read))

testFormat = FileFormat(0)
testFormat.write(testFile)

print("After:")
print(testFile.obj(AccessMode.Read, File.read))