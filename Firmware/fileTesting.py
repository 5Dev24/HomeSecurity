from src.file import File, FileSystem, FileFormat, AccessMode

testFile = File.getOrCreate(FileSystem, "test.dat")

print("Before:")
print(testFile.obj(AccessMode.Read, File.read))

testFormat = FileFormat(0)
testFormat.data.append("Test Data To Read")
testFormat.write(testFile)

print("After:")
print(testFile.obj(AccessMode.Read, File.read))

print("Attempting to load:")
