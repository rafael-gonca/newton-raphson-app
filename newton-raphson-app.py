import os
import json
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import sympy as sp

# FUNÇÕES DE LEITURA E GRAVAÇÃO DE DADOS

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DATA_FILE = os.path.join(BASE_DIR, "newton-raphson-app-data.json")

def carregar_dados():
    if not os.path.exists(DATA_FILE):
        return {"pastas": {"Exemplos": [{"nome": "Quadrática", "expressao": "x**2 - 2", "nota": "Apresentação: Raiz é aprox 1.4142"}]}}
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f: 
            return json.load(f)
    except: 
        return {"pastas": {}}

def salvar_dados(dados):
    with open(DATA_FILE, "w", encoding="utf-8") as f: 
        json.dump(dados, f, indent=4, ensure_ascii=False)

# FUNÇÕES MATEMÁTICAS

def criar_funcoes_numericas(expr_str):
    try:
        x_sym = sp.Symbol('x')
        f_sym = sp.sympify(expr_str)
        return sp.lambdify(x_sym, f_sym, 'numpy'), sp.lambdify(x_sym, sp.diff(f_sym, x_sym), 'numpy')
    except: return None, None

def metodo_bolzano(f, x_start=-100, x_end=100, passos=1000):
    intervalo = np.linspace(x_start, x_end, passos)
    for i in range(len(intervalo)-1):
        if f(intervalo[i]) * f(intervalo[i+1]) < 0:
            return (intervalo[i] + intervalo[i+1]) / 2
    return None

def newton_raphson_recursivo(f, df, xn, historico, limite=50):
    if limite == 0: return historico
    
    fn, dfn = f(xn), df(xn)
    
    # Condições de parada: derivada horizontal ou raiz já atingida com alta precisão
    if dfn == 0 or abs(fn) < 1e-12: return historico
    
    x_prox = xn - (fn / dfn)
    historico.append(x_prox)
    
    return newton_raphson_recursivo(f, df, x_prox, historico, limite - 1)

# FUNÇÕES QUE DESENHAM OS GRÁFICOS (E INTERAÇÃO)

def zoom_grafico(event, ax, canvas):
    if event.inaxes != ax or event.xdata is None or event.ydata is None: return
    escala = 1.3 if event.button == 'down' else (1/1.3 if event.button == 'up' else 1)
    xlim, ylim = ax.get_xlim(), ax.get_ylim()
    ax.set_xlim([event.xdata - (event.xdata - xlim[0]) * escala, event.xdata + (xlim[1] - event.xdata) * escala])
    ax.set_ylim([event.ydata - (event.ydata - ylim[0]) * escala, event.ydata + (ylim[1] - event.ydata) * escala])
    canvas.draw_idle()

class EstadoArraste:
    """Classe segregada para guardar os pixels durante o movimento do mouse na tela."""
    def __init__(self, ax, canvas):
        self.ax, self.canvas = ax, canvas
        self.press_ativo = False
        self.x0 = self.y0 = 0
        self.xlim_base = self.ylim_base = None
        
    def ao_pressionar(self, event):
        if event.inaxes != self.ax or event.button != 1: return
        self.press_ativo = True
        self.x0, self.y0 = event.x, event.y
        self.xlim_base, self.ylim_base = self.ax.get_xlim(), self.ax.get_ylim()
        
    def ao_mover(self, event):
        if not self.press_ativo or event.x is None or event.y is None: return
        inv = self.ax.transData.inverted()
        dx, dy = inv.transform((event.x, event.y)) - inv.transform((self.x0, self.y0))
        self.ax.set_xlim(self.xlim_base[0] - dx, self.xlim_base[1] - dx)
        self.ax.set_ylim(self.ylim_base[0] - dy, self.ylim_base[1] - dy)
        self.canvas.draw_idle()
        
    def ao_soltar(self, event):
        self.press_ativo = False

def ativar_interacao(ax, canvas):
    """Associa as funções visuais aos cliques e botões do sistema operacional."""
    arraste = EstadoArraste(ax, canvas)
    ax._arraste_obj = arraste # Prende o dado na memória local
    canvas.mpl_connect('scroll_event', lambda e: zoom_grafico(e, ax, canvas))
    canvas.mpl_connect('button_press_event', arraste.ao_pressionar)
    canvas.mpl_connect('motion_notify_event', arraste.ao_mover)
    canvas.mpl_connect('button_release_event', arraste.ao_soltar)

def desenhar_preview(ax, canvas, f):
    ax.clear()
    ax.grid(True, linestyle='--', alpha=0.5)
    ax.axhline(0, color='black', lw=0.5); ax.axvline(0, color='black', lw=0.5)
    ax.set_xlim(-100, 100); ax.set_ylim(-100, 100)
    if f:
        xv = np.linspace(-100, 100, 5000)
        yv = f(xv) if not isinstance(f(xv), (int, float)) else np.full_like(xv, f(xv))
        ax.plot(xv, yv, color='#1f77b4')
    canvas.draw()

def desenhar_simulacao(ax, canvas, f, historico, passo_atual, limites):
    ax.clear()
    ax.grid(True, linestyle='--', alpha=0.6)
    ax.axhline(0, color='black', lw=1); ax.axvline(0, color='black', lw=1)
    
    xv = np.linspace(-100, 100, 5000)
    yv = f(xv) if not isinstance(f(xv), (int, float)) else np.full_like(xv, f(xv))
    ax.plot(xv, yv, color='#1f77b4', alpha=0.8, label="f(x)")

    for i in range(passo_atual + 1):
        xn, fn = historico[i], f(historico[i])
        ax.plot(xn, fn, 'ro', markersize=5, zorder=5)
        ax.vlines(xn, 0, fn, color='gray', linestyle=':')
        if i < passo_atual:
            ax.plot([xn, historico[i+1]], [fn, 0], 'g--', linewidth=1.5)

    ax.set_xlim(limites[0]); ax.set_ylim(limites[1])
    canvas.draw()



# FUNÇÕES DE ENTRADAS E SAÍDAS (INTERFACE GUI)

class SimuladorNewton(tk.Toplevel):
    def __init__(self, master, funcao_dict, chute_inicial):
        super().__init__(master)
        self.funcao_dict = funcao_dict
        self.title(f"Simulação: f(x) = {funcao_dict['expressao']}")
        self.geometry("1100x750")
        
        self.f, self.df = criar_funcoes_numericas(funcao_dict['expressao'])
        
        # Injeção da lógica recursiva gerando o histórico único no arranque
        self.hist_completo = newton_raphson_recursivo(self.f, self.df, float(chute_inicial), [float(chute_inicial)])
        
        self.passo_atual = 0
        self.limites = ((-100, 100), (-100, 100))
        
        self.criar_widgets()
        self.atualizar_tela()

    def criar_widgets(self):
        paned = ttk.Panedwindow(self, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True)

        frm_esq = ttk.Frame(paned, padding=10)
        paned.add(frm_esq, weight=3)

        self.fig, self.ax = plt.subplots(figsize=(6, 5), dpi=100)
        self.canvas = FigureCanvasTkAgg(self.fig, master=frm_esq)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        ativar_interacao(self.ax, self.canvas)

        ctrl_frame = ttk.Frame(frm_esq)
        ctrl_frame.pack(fill=tk.X, pady=10)
        ttk.Button(ctrl_frame, text="<< Retroceder", command=self.retroceder).pack(side=tk.LEFT, padx=5)
        ttk.Button(ctrl_frame, text="Avançar >>", command=self.avancar).pack(side=tk.LEFT, padx=5)

        frm_dir = ttk.Frame(paned, padding=15)
        paned.add(frm_dir, weight=1)

        mf = ttk.LabelFrame(frm_dir, text=" Estatísticas ", padding=10)
        mf.pack(fill=tk.X, pady=(0, 10))
        self.lbl_sts = ttk.Label(mf, text="Iniciado", font=("Arial", 11, "bold"), foreground="gray")
        self.lbl_sts.pack(anchor=tk.W, pady=(0, 10))
        self.lbl_iter = ttk.Label(mf, text="Iteração: 0", font=("Arial", 12, "bold"))
        self.lbl_iter.pack(anchor=tk.W, pady=5)
        ttk.Label(mf, text="x (4 casas):").pack(anchor=tk.W, pady=(10, 0))
        self.lbl_x4 = ttk.Label(mf, font=("Consolas", 18), foreground="blue")
        self.lbl_x4.pack(anchor=tk.W)
        ttk.Label(mf, text="x (10 casas):").pack(anchor=tk.W, pady=(10, 0))
        self.lbl_x10 = ttk.Label(mf, font=("Consolas", 12), foreground="darkgreen")
        self.lbl_x10.pack(anchor=tk.W)

        nf = ttk.LabelFrame(frm_dir, text=" Notas ", padding=10)
        nf.pack(fill=tk.BOTH, expand=True)
        self.txt_nota = tk.Text(nf, wrap=tk.WORD, font=("Arial", 10), bg="#fafafa")
        self.txt_nota.insert(tk.END, self.funcao_dict.get("nota", ""))
        self.txt_nota.config(state=tk.DISABLED)
        self.txt_nota.pack(fill=tk.BOTH, expand=True, pady=5)
        self.btn_nota = ttk.Button(nf, text="📝 Editar Nota", command=self.editar_nota)
        self.btn_nota.pack(anchor=tk.E)

    def editar_nota(self):
        if self.txt_nota.cget("state") == "disabled":
            self.txt_nota.config(state=tk.NORMAL, bg="#ffffff")
            self.btn_nota.config(text="💾 Salvar Nota")
        else:
            self.funcao_dict["nota"] = self.txt_nota.get("1.0", tk.END).strip()
            salvar_dados(self.master.dados)
            self.txt_nota.config(state=tk.DISABLED, bg="#fafafa")
            self.btn_nota.config(text="📝 Editar Nota")

    def atualizar_tela(self):
        if self.passo_atual > 0: self.limites = (self.ax.get_xlim(), self.ax.get_ylim())
        
        desenhar_simulacao(self.ax, self.canvas, self.f, self.hist_completo, self.passo_atual, self.limites)

        x_atual = self.hist_completo[self.passo_atual]
        self.lbl_iter.config(text=f"Iteração: {self.passo_atual}")
        self.lbl_x4.config(text=f"{x_atual:.4f}")
        self.lbl_x10.config(text=f"{x_atual:.10f}")

        if self.passo_atual > 0:
            x_ant = self.hist_completo[self.passo_atual - 1]
            if f"{x_atual:.4f}" == f"{x_ant:.4f}": self.lbl_sts.config(text="RAIZ ENCONTRADA", foreground="green")
            else: self.lbl_sts.config(text="Calculando raiz")
        else:
            self.lbl_sts.config(text="Iniciado", foreground="gray")

    def avancar(self):
        if self.passo_atual < len(self.hist_completo) - 1:
            self.passo_atual += 1
            self.atualizar_tela()
        elif len(self.hist_completo) < 50:
            messagebox.showinfo("Fim", "O método já convergiu ou atingiu derivada nula.")

    def retroceder(self):
        if self.passo_atual > 0:
            self.passo_atual -= 1
            self.atualizar_tela()


class AppCalculo(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Newton-Raphson App")
        self.geometry("1200x750")
        self.dados = carregar_dados()
        self.pasta_sel = self.funcao_sel = None
        self.criar_layout()
        self.atualizar_tree()

    def criar_layout(self):
        sb = ttk.Frame(self, width=250, padding=10)
        sb.pack(side=tk.LEFT, fill=tk.Y)
        sb.pack_propagate(False)

        self.tree = ttk.Treeview(sb, show="tree", selectmode="browse")
        self.tree.pack(fill=tk.BOTH, expand=True)
        self.tree.bind("<<TreeviewSelect>>", self.selecionar_item)

        bf = ttk.Frame(sb)
        bf.pack(fill=tk.X, pady=5)
        ttk.Button(bf, text="Criar Pasta", command=self.add_pasta).grid(row=0, column=0, sticky="ew")
        ttk.Button(bf, text="Excluir Pasta", command=self.del_pasta).grid(row=0, column=1, sticky="ew")
        ttk.Button(bf, text="Criar Função", command=self.add_func).grid(row=1, column=0, sticky="ew")
        ttk.Button(bf, text="Excluir Função", command=self.del_func).grid(row=1, column=1, sticky="ew")
        ttk.Button(bf, text="Renomear", command=self.renomear_pasta).grid(row=2, column=0, columnspan=2, sticky="ew")
        bf.columnconfigure(0, weight=1); bf.columnconfigure(1, weight=1)

        cf = ttk.Frame(self, padding=20)
        cf.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.lbl_titulo = ttk.Label(cf, text="Selecione uma função", font=("Arial", 14, "bold"))
        self.lbl_titulo.pack(anchor=tk.W, pady=(0, 10))

        ff = ttk.Frame(cf)
        ff.pack(fill=tk.X, pady=5)
        ttk.Label(ff, text="Nome:").grid(row=0, column=0, sticky=tk.W)
        self.ent_nome = ttk.Entry(ff, font=("Arial", 11))
        self.ent_nome.grid(row=0, column=1, sticky=tk.EW, padx=5)
        ttk.Label(ff, text="f(x):").grid(row=1, column=0, sticky=tk.W)
        self.ent_expr = ttk.Entry(ff, font=("Consolas", 12))
        self.ent_expr.grid(row=1, column=1, sticky=tk.EW, padx=5)
        ff.columnconfigure(1, weight=1)
        ttk.Button(ff, text="Salvar", command=self.salvar_edicao).grid(row=0, column=2, rowspan=2, sticky=tk.NSEW)

        pf = ttk.LabelFrame(cf, text=" Preview ", padding=10)
        pf.pack(fill=tk.BOTH, expand=True, pady=10)
        self.fig_p, self.ax_p = plt.subplots(figsize=(4, 3))
        self.canvas_p = FigureCanvasTkAgg(self.fig_p, master=pf)
        self.canvas_p.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        ativar_interacao(self.ax_p, self.canvas_p)

        rs = ttk.LabelFrame(self, text=" Simulação ", padding=15, width=250)
        rs.pack(side=tk.RIGHT, fill=tk.Y)
        rs.pack_propagate(False)
        ttk.Label(rs, text="Chute (x0):").pack(anchor=tk.W, pady=(0, 15))
        ttk.Button(rs, text="Manual", command=self.iniciar_man).pack(fill=tk.X, pady=5)
        ttk.Button(rs, text="Bolzano", command=self.iniciar_bolz).pack(fill=tk.X, pady=5)

    def selecionar_item(self, event):
        sel = self.tree.selection()
        if not sel: return
        m = self.tree.item(sel[0], "values")
        if m[0] == "funcao":
            self.pasta_sel = m[1]
            self.funcao_sel = next(f for f in self.dados["pastas"][m[1]] if f["nome"] == m[2])
            self.lbl_titulo.config(text=f"Ativa: {m[2]}")
            self.ent_nome.delete(0, tk.END); self.ent_nome.insert(0, m[2])
            self.ent_expr.delete(0, tk.END); self.ent_expr.insert(0, self.funcao_sel["expressao"])
            f_func, _ = criar_funcoes_numericas(self.funcao_sel["expressao"])
            desenhar_preview(self.ax_p, self.canvas_p, f_func)
        else:
            self.pasta_sel = m[1]; self.funcao_sel = None
            self.lbl_titulo.config(text=f"Pasta: {m[1]}")

    def iniciar_man(self):
        if self.funcao_sel:
            x0 = simpledialog.askfloat("Chute", "Valor (x0):")
            if x0 is not None: SimuladorNewton(self, self.funcao_sel, x0)

    def iniciar_bolz(self):
        if self.funcao_sel:
            f, _ = criar_funcoes_numericas(self.funcao_sel["expressao"])
            x0 = metodo_bolzano(f) if f else None
            if x0 is not None: SimuladorNewton(self, self.funcao_sel, x0)
            else: messagebox.showerror("Erro", "Bolzano falhou.")

    def salvar_edicao(self):
        if self.funcao_sel:
            self.funcao_sel["nome"] = self.ent_nome.get().strip()
            self.funcao_sel["expressao"] = self.ent_expr.get().strip()
            salvar_dados(self.dados); self.atualizar_tree()
            f_func, _ = criar_funcoes_numericas(self.funcao_sel["expressao"])
            desenhar_preview(self.ax_p, self.canvas_p, f_func)

    def add_pasta(self):
        n = simpledialog.askstring("Nova Pasta", "Nome:")
        if n: self.dados["pastas"][n] = []; salvar_dados(self.dados); self.atualizar_tree()

    def del_pasta(self):
        if self.pasta_sel:
            del self.dados["pastas"][self.pasta_sel]; salvar_dados(self.dados); self.atualizar_tree()

    def add_func(self):
        if self.pasta_sel:
            n = simpledialog.askstring("Função", "Nome:")
            e = simpledialog.askstring("Função", "f(x):")
            if n and e: self.dados["pastas"][self.pasta_sel].append({"nome": n, "expressao": e, "nota": ""}); salvar_dados(self.dados); self.atualizar_tree()

    def del_func(self):
        if self.funcao_sel:
            self.dados["pastas"][self.pasta_sel] = [f for f in self.dados["pastas"][self.pasta_sel] if f['nome'] != self.funcao_sel['nome']]
            salvar_dados(self.dados); self.atualizar_tree()

    def renomear_pasta(self):
        if self.pasta_sel:
            nn = simpledialog.askstring("Renomear", "Novo nome:", initialvalue=self.pasta_sel)
            if nn: self.dados["pastas"][nn] = self.dados["pastas"].pop(self.pasta_sel); self.pasta_sel = nn; salvar_dados(self.dados); self.atualizar_tree()

    def atualizar_tree(self):
        for i in self.tree.get_children(): self.tree.delete(i)
        for p, fs in self.dados["pastas"].items():
            id_p = self.tree.insert("", "end", text=f" {p}", values=("pasta", p), open=True)
            for f in fs: self.tree.insert(id_p, "end", text=f" {f['nome']}", values=("funcao", p, f['nome']))

# EXECUÇÃO PRINCIPAL

def main():
    app = AppCalculo()
    app.mainloop()

if __name__ == "__main__":
    main()
