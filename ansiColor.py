#! /usr/bin/python3

def print_256_colors():
    for i in range(0, 256):
        print(f"\033[38;5;{i}m {i:3} \033[0m", end="")
        if (i + 1) % 16 == 0:
            print()

def print_true_colors():
    step = 51  # Adjust for fewer/more steps
    for r in range(0, 256, step):
        for g in range(0, 256, step):
            for b in range(0, 256, step):
                print(f"\033[38;2;{r};{g};{b}m True Color: ({r},{g},{b}) \033[0m")


if __name__=="__main__":
    print_256_colors()
    # print_true_colors()

