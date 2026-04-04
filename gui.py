import tkinter as tk
from tkinter import ttk, messagebox

from codecs_impl import AVAILABLE_CODECS, get_codec_by_name, get_codec_names

class App(tk.Tk):
    # janela principal
    def __init__(self):
        super().__init__()
        self.title("Codificacao e Decodificacao")
        self.minsize(700, 600)
        self.resizable(True, True)

        self.current_codec = None
        self.param_widgets = {}  # name -> widget
        self.last_encoded = []   # lista de codewords do ultimo encode

        self._build_ui()
        self._on_codec_changed()  # inicializa com o primeiro codec

    def _build_ui(self):
        main = ttk.Frame(self, padding=12)
        main.pack(fill=tk.BOTH, expand=True)

        # selecao do metodo
        method_frame = ttk.LabelFrame(main, text="Metodo de Codificacao", padding=8)
        method_frame.pack(fill=tk.X, pady=(0, 8))

        self.codec_var = tk.StringVar()
        codec_names = get_codec_names()
        self.codec_var.set(codec_names[0])

        ttk.Label(method_frame, text="Algoritmo:").pack(side=tk.LEFT, padx=(0, 6))
        self.codec_combo = ttk.Combobox(
            method_frame,
            textvariable=self.codec_var,
            values=codec_names,
            state="readonly",
            width=20,
        )
        self.codec_combo.pack(side=tk.LEFT)
        self.codec_combo.bind("<<ComboboxSelected>>", lambda e: self._on_codec_changed())

        # descricao
        self.desc_label = ttk.Label(method_frame, text="", foreground="gray")
        self.desc_label.pack(side=tk.LEFT, padx=(12, 0))

        # parametros extras
        self.params_frame = ttk.LabelFrame(main, text="Parametros", padding=8)
        self.params_frame.pack(fill=tk.X, pady=(0, 8))

        # entrada
        input_frame = ttk.LabelFrame(main, text="Entrada", padding=8)
        input_frame.pack(fill=tk.X, pady=(0, 8))

        self.input_hint = ttk.Label(input_frame, text="", foreground="gray")
        self.input_hint.pack(anchor=tk.W)

        self.input_text = tk.Text(input_frame, height=3, font=("Courier", 12))
        self.input_text.pack(fill=tk.X, pady=(4, 0))

        # botoes de acao
        btn_frame = ttk.Frame(input_frame)
        btn_frame.pack(fill=tk.X, pady=(8, 0))

        self.encode_btn = ttk.Button(btn_frame, text="Codificar", command=self._do_encode)
        self.encode_btn.pack(side=tk.LEFT, padx=(0, 6))

        self.decode_btn = ttk.Button(btn_frame, text="Decodificar", command=self._do_decode)
        self.decode_btn.pack(side=tk.LEFT)

        self.clear_btn = ttk.Button(btn_frame, text="Limpar Tudo", command=self._clear_all)
        self.clear_btn.pack(side=tk.RIGHT)

        # resultado
        result_frame = ttk.LabelFrame(main, text="Resultado", padding=8)
        result_frame.pack(fill=tk.X, pady=(0, 8))

        self.result_text = tk.Text(
            result_frame, height=4, font=("Courier", 12), state=tk.DISABLED,

        )
        self.result_text.pack(fill=tk.X)

        # insercao de erro
        error_frame = ttk.LabelFrame(main, text="Insercao de Erro", padding=8)
        error_frame.pack(fill=tk.X, pady=(0, 8))

        err_top = ttk.Frame(error_frame)
        err_top.pack(fill=tk.X)

        ttk.Label(err_top, text="Posicoes dos bits a inverter (virgula-separadas):").pack(
            side=tk.LEFT, padx=(0, 6)
        )
        self.error_entry = ttk.Entry(err_top, width=30, font=("Courier", 11))
        self.error_entry.pack(side=tk.LEFT, padx=(0, 6))

        ttk.Label(err_top, text="(0-indexed)", foreground="gray").pack(side=tk.LEFT)

        err_btn_frame = ttk.Frame(error_frame)
        err_btn_frame.pack(fill=tk.X, pady=(6, 0))

        self.apply_error_btn = ttk.Button(
            err_btn_frame, text="Aplicar Erro", command=self._apply_error
        )
        self.apply_error_btn.pack(side=tk.LEFT, padx=(0, 6))

        self.decode_error_btn = ttk.Button(
            err_btn_frame, text="Decodificar com Erro", command=self._decode_with_error
        )
        self.decode_error_btn.pack(side=tk.LEFT)

        # resultado com erro
        self.error_result_text = tk.Text(
            error_frame, height=4, font=("Courier", 12), state=tk.DISABLED,

        )
        self.error_result_text.pack(fill=tk.X, pady=(6, 0))

        # log/mensagens
        log_frame = ttk.LabelFrame(main, text="Logs", padding=8)
        log_frame.pack(fill=tk.BOTH, expand=True)

        self.log_text = tk.Text(
            log_frame, height=4, font=("Courier", 10), state=tk.DISABLED,
            fg="gray30"
        )
        self.log_text.pack(fill=tk.BOTH, expand=True)

    def _set_result(self, text: str):
        self.result_text.config(state=tk.NORMAL)
        self.result_text.delete("1.0", tk.END)
        self.result_text.insert("1.0", text)
        self.result_text.config(state=tk.DISABLED)

    def _set_error_result(self, text: str):
        self.error_result_text.config(state=tk.NORMAL)
        self.error_result_text.delete("1.0", tk.END)
        self.error_result_text.insert("1.0", text)
        self.error_result_text.config(state=tk.DISABLED)

    def _log(self, msg: str):
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, msg + "\n")
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)

    def _clear_all(self):
        self.input_text.delete("1.0", tk.END)
        self._set_result("")
        self._set_error_result("")
        self.error_entry.delete(0, tk.END)
        self.last_encoded = []
        self.log_text.config(state=tk.NORMAL)
        self.log_text.delete("1.0", tk.END)
        self.log_text.config(state=tk.DISABLED)

    def _get_params(self) -> dict:
        # valida os parametros recebidos do usuario e retorna em formato dict para passar para o codec
        params = {}
        codec = get_codec_by_name(self.codec_var.get())
        if codec is None:
            return params

        for cfg in codec.get_params_config():
            name = cfg["name"]
            widget = self.param_widgets.get(name)
            if widget is None:
                continue
            raw = widget.get().strip()
            if cfg["type"] == "int":
                try:
                    val = int(raw)
                except ValueError:
                    raise ValueError(
                        f"Parametro '{cfg['label']}' deve ser inteiro. Valor: '{raw}'"
                    )
                mn = cfg.get("min")
                mx = cfg.get("max")
                if mn is not None and val < mn:
                    raise ValueError(f"Parametro '{cfg['label']}' deve ser >= {mn}. Valor: {val}")
                if mx is not None and val > mx:
                    raise ValueError(f"Parametro '{cfg['label']}' deve ser <= {mx}. Valor: {val}")
                params[name] = val
            elif cfg["type"] == "float":
                try:
                    params[name] = float(raw)
                except ValueError:
                    raise ValueError(
                        f"Parametro '{cfg['label']}' deve ser numerico. Valor: '{raw}'"
                    )
            else:
                params[name] = raw
        return params

    def _on_codec_changed(self):
        codec = get_codec_by_name(self.codec_var.get())
        if codec is None:
            return
        self.current_codec = codec
        self.desc_label.config(text=codec.description)

        if codec.name == "Huffman":
            self.input_hint.config(
                text="Digite a string a ser codificada (ou codeword binaria para decodificar)"
            )
        else:
            self.input_hint.config(
                text="Digite valores separados por espaco (ou codewords binarias para decodificar)"
            )

        # rebuild dos param
        for w in self.params_frame.winfo_children():
            w.destroy()
        self.param_widgets.clear()

        configs = codec.get_params_config()
        if not configs:
            ttk.Label(self.params_frame, text="Nenhum parametro extra.", foreground="gray").pack(
                anchor=tk.W
            )
        else:
            for cfg in configs:
                row = ttk.Frame(self.params_frame)
                row.pack(fill=tk.X, pady=2)
                ttk.Label(row, text=cfg["label"] + ":").pack(side=tk.LEFT, padx=(0, 6))
                entry = ttk.Entry(row, width=10, font=("Courier", 11))
                entry.insert(0, str(cfg.get("default", "")))
                entry.pack(side=tk.LEFT)
                self.param_widgets[cfg["name"]] = entry

                hints = []
                if "min" in cfg:
                    hints.append(f"min={cfg['min']}")
                if "max" in cfg:
                    hints.append(f"max={cfg['max']}")
                if hints:
                    ttk.Label(row, text=f"  ({', '.join(hints)})", foreground="gray").pack(
                        side=tk.LEFT
                    )

    def _do_encode(self):
        codec = self.current_codec
        if codec is None:
            return

        raw_input = self.input_text.get("1.0", tk.END).strip()

        # validacao por encoder
        valid, msg = codec.validate_encode_input(raw_input)
        if not valid:
            messagebox.showerror("Erro de Validacao", msg)
            self._log(f"[ERRO] Validacao: {msg}")
            return

        try:
            params = self._get_params()
        except ValueError as e:
            messagebox.showerror("Erro de Parametro", str(e))
            self._log(f"[ERRO] Parametro: {e}")
            return

        # efetivamente codifica usando o codec selecionado
        try:
            values = codec.parse_encode_input(raw_input)
            codewords = []
            for val in values:
                cw = codec.encode(val, **params)
                codewords.append(cw)

            self.last_encoded = codewords
            result_str = " ".join(codewords)
            self._set_result(result_str)

            # log
            self._log(f"[ENCODE] {codec.name} | Entrada: {raw_input} | Params: {params}")
            for val, cw in zip(values, codewords):
                self._log(f"  {val} -> {cw} ({len(cw)} bits)")

        except NotImplementedError as e:
            messagebox.showwarning("Nao Implementado", str(e))
            self._log(f"[AVISO] {e}")
        except Exception as e:
            messagebox.showerror("Erro na Codificacao", str(e))
            self._log(f"[ERRO] Codificacao: {e}")

    def _do_decode(self):
        codec = self.current_codec
        if codec is None:
            return

        raw_input = self.input_text.get("1.0", tk.END).strip()

        # validacao por decoder
        valid, msg = codec.validate_decode_input(raw_input)
        if not valid:
            messagebox.showerror("Erro de Validacao", msg)
            self._log(f"[ERRO] Validacao: {msg}")
            return

        try:
            params = self._get_params()
        except ValueError as e:
            messagebox.showerror("Erro de Parametro", str(e))
            self._log(f"[ERRO] Parametro: {e}")
            return

        # efetivamente decodifica usando o codec selecionado
        try:
            codewords = codec.parse_decode_input(raw_input)
            results = []
            for cw in codewords:
                val = codec.decode(cw, **params)
                results.append(str(val))

            result_str = " ".join(results)
            self._set_result(result_str)

            self._log(f"[DECODE] {codec.name} | Entrada: {raw_input} | Params: {params}")
            for cw, val in zip(codewords, results):
                self._log(f"  {cw} -> {val}")

        except NotImplementedError as e:
            messagebox.showwarning("Nao Implementado", str(e))
            self._log(f"[AVISO] {e}")
        except Exception as e:
            messagebox.showerror("Erro na Decodificacao", str(e))
            self._log(f"[ERRO] Decodificacao: {e}")

    def _flip_bits(self, codeword: str, positions: list[int]) -> str:
        # inverte os bits indicados
        bits = list(codeword)
        for pos in positions:
            if 0 <= pos < len(bits):
                bits[pos] = '1' if bits[pos] == '0' else '0'
        return ''.join(bits)

    def _parse_error_positions(self) -> list[int]:
        raw = self.error_entry.get().strip()
        if not raw:
            raise ValueError("Insira as posicoes dos bits a inverter (separadas por virgula).")

        positions = []
        for token in raw.split(","):
            token = token.strip()
            if not token:
                continue
            try:
                pos = int(token)
            except ValueError:
                raise ValueError(f"Posicao invalida: '{token}'. Deve ser inteiro.")
            if pos < 0:
                raise ValueError(f"Posicao deve ser >= 0. Valor: {pos}")
            positions.append(pos)

        if not positions:
            raise ValueError("Nenhuma posicao valida fornecida.")
        return positions

    def _apply_error(self):
        if not self.last_encoded:
            messagebox.showinfo(
                "Sem Dados",
                "Primeiro codifique algum valor para poder inserir erros."
            )
            return

        try:
            positions = self._parse_error_positions()
        except ValueError as e:
            messagebox.showerror("Erro", str(e))
            self._log(f"[ERRO] {e}")
            return

        full_cw = "".join(self.last_encoded)
        corrupted = self._flip_bits(full_cw, positions)

        corrupted_parts = []
        offset = 0
        for cw in self.last_encoded:
            corrupted_parts.append(corrupted[offset:offset + len(cw)])
            offset += len(cw)

        self._set_error_result(
            f"Original:    {' '.join(self.last_encoded)}\n"
            f"Com erro:    {' '.join(corrupted_parts)}\n"
            f"Posicoes invertidas: {positions}"
        )

        self._log(
            f"[ERRO INSERIDO] Posicoes: {positions} | "
            f"Original: {''.join(self.last_encoded)} | "
            f"Corrompido: {corrupted}"
        )

        self._corrupted_parts = corrupted_parts

    def _decode_with_error(self):
        if not hasattr(self, '_corrupted_parts') or not self._corrupted_parts:
            messagebox.showinfo(
                "Sem Dados",
                "Primeiro aplique um erro nos codewords codificados."
            )
            return

        codec = self.current_codec
        if codec is None:
            return

        try:
            params = self._get_params()
        except ValueError as e:
            messagebox.showerror("Erro de Parametro", str(e))
            return

        results = []
        errors = []
        for cw in self._corrupted_parts:
            try:
                val = codec.decode(cw, **params)
                results.append(str(val))
            except NotImplementedError as e:
                messagebox.showwarning("Nao Implementado", str(e))
                self._log(f"[AVISO] {e}")
                return
            except Exception as e:
                results.append(f"ERRO({e})")
                errors.append(str(e))

        current = self.error_result_text.get("1.0", tk.END).strip()
        self._set_error_result(
            current + f"\nDecodificado: {' '.join(results)}"
        )

        self._log(f"[DECODE c/ ERRO] Resultado: {' '.join(results)}")
        if errors:
            for err in errors:
                self._log(f"  [ERRO] {err}")
