# Compiler settings - Can change to clang++ if desired
CXX = g++ 

# Compilation flags - Wall shows all warnings; c++17 is the language standard
CXXFLAGS = -Wall 
#-std=c++17

# Linker flags - Can add libraries here with -l
LDFLAGS = -lsodium 

# Source files - List your cpp source files here
SOURCES = commitment.cpp

# Object files - Converts the .cpp filenames to .o
OBJECTS = $(SOURCES:.cpp=.o)

# Header files - Not necessary unless you have specific dependencies
#HEADERS = 

# The final build target executable
TARGET = ringct_app

# Default target
all: $(TARGET)

# Rule to link the program
$(TARGET): $(OBJECTS)
	$(CXX) $(LDFLAGS) -o $@ $^

# Rule to compile the source files
%.o: %.cpp #$(HEADERS)
	$(CXX) $(CXXFLAGS) -c $<

# Clean workspace
clean:
	rm -f $(OBJECTS) $(TARGET)

# Rule for making a debug build
debug: CXXFLAGS += -g
debug: $(TARGET)

# Include dependencies
-include $(OBJECTS:.o=.d)

# Rule to generate a dependency file by using the C++ preprocessor
%.d: %.cpp
	$(CXX) $(CXXFLAGS) -MM -MT $(@:.d=.o) $< > $@
