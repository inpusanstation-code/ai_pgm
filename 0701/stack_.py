#stack memory demonstration

stack = []

def push(stack, item):
    """Push an item onto the stack."""
    stack.append(item)
    
def pop(stack):
    """Pop an item from the stack."""
    if stack:
        return stack.pop()
    else:
        raise IndexError("pop from empty stack")
def peek(stack):
    """Peek at the top item of the stack without removing it."""
    if stack:
        return stack[-1]
    else:
        raise IndexError("peek from empty stack")
    
def is_empty(stack):
    """Check if the stack is empty."""
    print(f"Stack is empty: {len(stack) == 0}")
    return len(stack) == 0

def size(stack):
    """Return the size of the stack."""
    print(f"Stack size: {len(stack)}")
    return len(stack)

def visualize_stack(stack):
    """Visualize the stack."""
    print("Stack (top to bottom):")
    for item in reversed(stack):
        print(f"| {item} |")
    print(" ----- ")
       
    
if __name__ == "__main__":
    while True:
        print("1. Push 2. Pop 3. Peek 4. Is Empty 5. Size 6. Visualize Stack 7. Exit ")   
        choice = input("Enter your choice: ")
        if choice == '1':
            item = input("Enter item to push: ")
            push(stack, item)
            visualize_stack(stack)
        elif choice == '2':
            try:
                popped_item = pop(stack)
                print(f"Popped item: {popped_item}")
                visualize_stack(stack)
            except IndexError as e:
                print(e)
        elif choice == '3':
            try:
                top_item = peek(stack)
                print(f"Top item: {top_item}")
            except IndexError as e:
                print(e)
        elif choice == '4':
            is_empty(stack)
        elif choice == '5':
            size(stack)
        elif choice == '6':
            visualize_stack(stack)
        elif choice == '7':
            print("Exiting...")
            break
    