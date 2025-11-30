import tkinter as tk
from transform_tools import CircularButton

def test_click():
    print("PASS: Button clicked")

root = tk.Tk()
btn = CircularButton(root, label_text="Mirror", command=test_click)
btn.pack()

# Simulate click on label
# Label is at (size/2, size + 10)
# Default size is 60. So (30, 70).
print("Simulating click on label...")
# We can't easily simulate a click event on a specific item without a GUI test driver.
# But we can verify the bindings.

tags = btn.gettags(btn.label)
print(f"Label tags: {tags}")
bindings = btn.tag_bind(btn.label, "<Button-1>")
print(f"Label binding: {bindings}")

if not bindings:
    print("FAIL: Label has no binding")
else:
    print("PASS: Label has binding")

root.destroy()
