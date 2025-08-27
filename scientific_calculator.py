import tkinter as tk
from tkinter import ttk, messagebox
import math
import re

# ---------------------------
# Safe evaluation helpers
# ---------------------------

# Mode for trig: 'rad' or 'deg'
TRIG_MODE = 'deg'  # default degree mode

# Wrap trig functions to respect TRIG_MODE
def _wrap_trig(fn):
    def inner(x):
        try:
            val = float(x)
        except Exception:
            raise ValueError("Invalid value for trig")
        if TRIG_MODE == 'deg':
            val = math.radians(val)
        return fn(val)
    return inner

def _wrap_itrig(fn):
    # inverse trig returns radians -> convert to degrees if needed
    def inner(x):
        val = float(x)
        result = fn(val)
        if TRIG_MODE == 'deg':
            result = math.degrees(result)
        return result
    return inner

# Custom factorial that works for integers only
def factorial(x):
    x = float(x)
    if not x.is_integer() or x < 0:
        raise ValueError("Factorial only defined for non-negative integers")
    return math.factorial(int(x))

# Create a dictionary of safe names exposed to eval
SAFE_NAMES = {
    'sin': _wrap_trig(math.sin),
    'cos': _wrap_trig(math.cos),
    'tan': _wrap_trig(math.tan),
    'asin': _wrap_itrig(math.asin),
    'acos': _wrap_itrig(math.acos),
    'atan': _wrap_itrig(math.atan),
    'sqrt': math.sqrt,
    'log': math.log,        # natural log
    'ln': math.log,
    'log10': math.log10,
    'exp': math.exp,
    'pow': pow,
    'abs': abs,
    'factorial': factorial,
    'fact': factorial,
    'pi': math.pi,
    'e': math.e,
}

# Evaluate expression safely
def safe_eval(expr):
    # Replace caret '^' with '**'
    expr = expr.replace('^', '**')

    # Replace percentage like '50%' with '(50/100)'
    expr = re.sub(r'(\d+(\.\d+)?)\s*%', r'(\1/100)', expr)

    # Replace unary factorial 'n!' -> factorial(n)
    # Handles things like 5! or (3+2)!
    expr = re.sub(r'(\([^()]+\)|\d+(\.\d+)?)\s*!', r'factorial(\1)', expr)

    # Disallow characters that are not digits, operators, parentheses, letters, dots, or underscores
    if re.search(r'[^0-9A-Za-z\.\+\-\*\/\^\%\(\)\,\!\_\s]', expr):
        raise ValueError("Invalid characters in expression")

    # Evaluate using restricted globals and our SAFE_NAMES as locals
    try:
        result = eval(expr, {"__builtins__": None}, SAFE_NAMES)
    except Exception as e:
        raise e
    return result

# ---------------------------
# GUI
# ---------------------------

class SciCalculator(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Advanced Scientific Calculator")
        self.resizable(False, False)
        self.configure(padx=8, pady=8)

        self.memory = 0.0
        self.history = []

        # Entry
        self.entry_var = tk.StringVar()
        entry_frame = ttk.Frame(self)
        entry_frame.grid(row=0, column=0, columnspan=6, sticky="nsew")
        self.entry = ttk.Entry(entry_frame, textvariable=self.entry_var, font=("Consolas", 18), justify="right", width=30)
        self.entry.pack(fill="both", expand=True, ipady=8)

        # Status / trig mode
        self.mode_var = tk.StringVar(value=TRIG_MODE.upper())
        mode_label = ttk.Label(self, textvariable=self.mode_var, width=7, anchor="center")
        mode_label.grid(row=1, column=0, columnspan=2, sticky="we", pady=(4,0))

        # Buttons layout
        btn_cfg = {'padx':6, 'pady':6}
        buttons = [
            ('MC', 1,0), ('MR', 1,1), ('M+',1,2), ('M-',1,3), ('%',1,4), ('⌫',1,5),
            ('7',2,0), ('8',2,1), ('9',2,2), ('/',2,3), ('sqrt',2,4), ('^',2,5),
            ('4',3,0), ('5',3,1), ('6',3,2), ('*',3,3), ('(',3,4), (')',3,5),
            ('1',4,0), ('2',4,1), ('3',4,2), ('-',4,3), ('pi',4,4), ('e',4,5),
            ('0',5,0), ('.',5,1), ('+/-',5,2), ('+',5,3), ('ln',5,4), ('log10',5,5),
            ('sin',6,0), ('cos',6,1), ('tan',6,2), ('asin',6,3), ('acos',6,4), ('atan',6,5),
            ('!',7,0), ('exp',7,1), ('abs',7,2), ('C',7,3), ('CE',7,4), ('=',7,5),
        ]

        for (text, r, c) in buttons:
            b = ttk.Button(self, text=text, command=lambda t=text: self.on_button(t))
            b.grid(row=r+0, column=c, sticky="nsew", **btn_cfg)

        # Make grid expand equally
        for i in range(6):
            self.grid_columnconfigure(i, weight=1)
        for r in range(1, 9):
            self.grid_rowconfigure(r, weight=1)

        # History box
        hist_label = ttk.Label(self, text="History")
        hist_label.grid(row=9, column=0, columnspan=3, sticky="w", pady=(8,0))
        self.hist_list = tk.Listbox(self, height=6, activestyle='none')
        self.hist_list.grid(row=10, column=0, columnspan=4, sticky="nsew", pady=(2,0))
        self.hist_list.bind('<Double-Button-1>', self.use_history_item)

        # Degree/Radian toggle
        self.trig_btn = ttk.Button(self, text="Toggle Deg/Rad", command=self.toggle_trig_mode)
        self.trig_btn.grid(row=9, column=4, columnspan=2, sticky="nsew", pady=(8,0))

        # Keyboard support
        self.bind_all("<Return>", lambda e: self.on_button('='))
        self.bind_all("<BackSpace>", lambda e: self.on_button('⌫'))
        self.bind_all("<Escape>", lambda e: self.on_button('C'))

    # ---------------------------
    # Button actions
    # ---------------------------
    def on_button(self, label):
        text = self.entry_var.get()
        if label == 'C':
            self.entry_var.set('')
        elif label == 'CE':
            self.entry_var.set('')
            self.history.clear()
            self.hist_list.delete(0, tk.END)
        elif label == '⌫':
            self.entry_var.set(text[:-1])
        elif label == '+/-':
            # toggle sign of last number in expression (simple approach)
            try:
                if text.strip() == '':
                    return
                # If entire text is a number:
                val = float(text)
                val = -val
                self.entry_var.set(str(val))
            except Exception:
                # fallback: append *(-1)
                self.entry_var.set(text + "*(-1)")
        elif label in ('7','8','9','4','5','6','1','2','3','0','.','+','-','*','/','(',')','^',','):
            self.entry_var.set(text + label)
        elif label == '%':
            self.entry_var.set(text + '%')
        elif label == 'pi':
            self.entry_var.set(text + 'pi')
        elif label == 'e':
            self.entry_var.set(text + 'e')
        elif label in ('sin','cos','tan','asin','acos','atan','sqrt','ln','log10','exp','abs','factorial','!','log'):
            # map ! to factorial insertion
            if label == '!':
                self.entry_var.set(text + '!')
            else:
                # function insertion: add function and opening parenthesis
                self.entry_var.set(text + label + '(')
        elif label == 'sqrt':
            self.entry_var.set(text + 'sqrt(')
        elif label == 'log10':
            self.entry_var.set(text + 'log10(')
        elif label == 'ln':
            self.entry_var.set(text + 'ln(')
        elif label == 'exp':
            self.entry_var.set(text + 'exp(')
        elif label == 'abs':
            self.entry_var.set(text + 'abs(')
        elif label == 'factorial':
            self.entry_var.set(text + 'factorial(')
        elif label == '=':
            self.calculate()
        elif label == 'MC':
            self.memory = 0.0
            messagebox.showinfo("Memory", "Memory cleared")
        elif label == 'MR':
            # recall
            self.entry_var.set(text + str(self.memory))
        elif label == 'M+':
            # add current evaluated value to memory
            try:
                value = safe_eval(text)
                self.memory += float(value)
                messagebox.showinfo("Memory", f"Added {value} to memory")
            except Exception as e:
                messagebox.showerror("Error", f"Cannot add to memory: {e}")
        elif label == 'M-':
            try:
                value = safe_eval(text)
                self.memory -= float(value)
                messagebox.showinfo("Memory", f"Subtracted {value} from memory")
            except Exception as e:
                messagebox.showerror("Error", f"Cannot subtract from memory: {e}")
        else:
            # fallback
            self.entry_var.set(text + label)

    def toggle_trig_mode(self):
        global TRIG_MODE, SAFE_NAMES
        if TRIG_MODE == 'deg':
            TRIG_MODE = 'rad'
        else:
            TRIG_MODE = 'deg'
        # rebuild SAFE_NAMES trig wrappers to reflect mode
        SAFE_NAMES.update({
            'sin': _wrap_trig(math.sin),
            'cos': _wrap_trig(math.cos),
            'tan': _wrap_trig(math.tan),
            'asin': _wrap_itrig(math.asin),
            'acos': _wrap_itrig(math.acos),
            'atan': _wrap_itrig(math.atan),
        })
        self.mode_var.set(TRIG_MODE.upper())

    def calculate(self):
        expr = self.entry_var.get().strip()
        if not expr:
            return
        try:
            result = safe_eval(expr)
            # format floats nicely
            if isinstance(result, float):
                # remove trailing zeros
                result = round(result, 12)
                # if integer after rounding, make int
                if float(result).is_integer():
                    result = int(result)
            self.entry_var.set(str(result))
            # add to history
            self.history.append((expr, result))
            self.hist_list.insert(tk.END, f"{expr} = {result}")
            # auto-scroll to bottom
            self.hist_list.yview_moveto(1)
        except Exception as e:
            messagebox.showerror("Error", f"Could not evaluate expression:\n{e}")

    def use_history_item(self, event):
        sel = self.hist_list.curselection()
        if not sel:
            return
        idx = sel[0]
        expr, result = self.history[idx]
        self.entry_var.set(str(expr))

# ---------------------------
# Run the app
# ---------------------------

if __name__ == "__main__":
    app = SciCalculator()
    app.mainloop()
