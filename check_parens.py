import io
import tokenize

with open(r'D:\PROJECT\WEB\LOBN_exam_speech_board_reflex\LOBN_exam_speech_board_reflex\pages\admin.py', 'r') as f:
    source = f.read()

stack = []
for tok in tokenize.generate_tokens(io.StringIO(source).readline):
    if tok.type == tokenize.OP:
        if tok.string in '([{':
            stack.append((tok.string, tok.start[0]))
        elif tok.string in ')]}':
            if stack:
                stack.pop()
            else:
                print(f"Extra closing {tok.string} at line {tok.start[0]}")

for ch, line in stack:
    print(f"Unclosed {ch} at line {line}")
