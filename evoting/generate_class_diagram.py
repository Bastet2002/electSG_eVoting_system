# generate_class_diagram.py

import os
import subprocess

def generate_class_diagram(paths):
    # Run pyreverse to generate UML diagrams
    try:
        subprocess.run([
            "pyreverse",
            "-o", "png",  # Output format
            "-p", "DjangoProject",  # Project name
        ] + paths,  # The paths/modules to analyze
        check=True)
        print(f"Class diagrams for {', '.join(paths)} generated successfully.")
    except subprocess.CalledProcessError as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    paths = ["myapp", "myapp/views.py"]  # Replace with your Django app names or paths
    generate_class_diagram(paths)
