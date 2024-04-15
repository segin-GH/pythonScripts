#! /usr/bin/python3


def print_256_colors_for_c():
    for i in range(0, 256):
        # Constructing the escape sequence for C with double backslashes
        c_escape_sequence = f"\\033[38;5;{i}m"
        # Displaying the color, its number, and the C escape sequence
        print(f"\033[38;5;{i}m {i:3} {c_escape_sequence} \033[0m")
        if (i + 1) % 16 == 0:
            print()


def print_true_colors():
    step = 51  # Adjust for fewer/more steps
    for r in range(0, 256, step):
        for g in range(0, 256, step):
            for b in range(0, 256, step):
                print(f"\033[38;2;{r};{g};{b}m True Color: ({r},{g},{b}) \033[0m")


# print the colors with ansi code
def print_ansi_colors():
    for i in range(0, 8):
        print(f"\033[3{i}m {i} \033[0m", end="")
    print()
    for i in range(0, 8):
        print(f"\033[4{i}m {i} \033[0m", end="")
    print()


if __name__ == "__main__":
    print_256_colors_for_c()
    #  print_true_colors()
    #  print_ansi_colors()
