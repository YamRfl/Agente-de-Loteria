import argparse
import os
from src import inicializar_bd, atualizar_resultados, gerar_relatorio_estatistico, sugerir_jogo, conferir_apostas_pendentes
from src.generator import calcular_custo_jogos

def main():
    inicializar_bd()

    parser = argparse.ArgumentParser(description="Agente de IA - Analista de Loterias Caixa")
    parser.add_argument("--update", choices=['megasena', 'lotofacil', 'quina'], help="Atualiza os resultados")
    parser.add_argument("--analyze", choices=['megasena', 'lotofacil', 'quina'], help="Exibe estatísticas")
    parser.add_argument("--suggest", choices=['megasena', 'lotofacil', 'quina'], help="Gera sugestão de jogo")
    parser.add_argument("--check", action="store_true", help="Confere as apostas")

    args = parser.parse_args()

    if args.update:
        atualizar_resultados(args.update)
        
    elif args.analyze:
        gerar_relatorio_estatistico(args.analyze)
        
    elif args.suggest:
        print(f"\n[*] Iniciando o gerador de bilhetes para a {args.suggest.upper()}...")
        
        bilhete_completo = []
        custo_total = 0.0
        
        # --- INÍCIO DO LOOP ---
        while True:
            try:
                entrada_jogos = input("\n-> Quantos jogos deseja gerar agora? (Pressione Enter para apenas 1): ")
                qtd_jogos = int(entrada_jogos) if entrada_jogos.strip() else 1
                
                entrada_dezenas = input(f"-> Quantas dezenas por jogo? (Pressione Enter para o padrão): ")
                qtd_dezenas = int(entrada_dezenas) if entrada_dezenas.strip() else None
                
                print(f"[*] A calcular {qtd_jogos} sugestão(ões)...")
                jogos_lote = sugerir_jogo(args.suggest, qtd_jogos, qtd_dezenas)
                
                if isinstance(jogos_lote, str):
                    print(jogos_lote) # Mostra o erro se pedir dezenas a mais/a menos
                else:
                    # Calcula o preço deste lote e adiciona ao total
                    dezenas_reais = len(jogos_lote[0])
                    custo_lote = calcular_custo_jogos(args.suggest, qtd_jogos, dezenas_reais)
                    custo_total += custo_lote
                    
                    # Guarda os jogos na lista mestra do bilhete
                    for jogo in jogos_lote:
                        bilhete_completo.append((dezenas_reais, jogo))
                        
                    print(f"[V] {qtd_jogos} jogo(s) de {dezenas_reais} dezenas adicionado(s) ao carrinho!")

            except ValueError:
                print("[!] Erro: Por favor, digite apenas números válidos.")
                continue # Se der erro, volta para o início da pergunta sem fechar o programa
                
            # A pergunta mágica que controla o loop
            continuar = input("\n-> Deseja gerar MAIS apostas para este bilhete? (S/N): ")
            if continuar.strip().upper() != 'S':
                break # Quebra o loop e vai para o fechamento da conta
        # --- FIM DO LOOP ---
        
        
        # --- CÁLCULO FINAL E EXPORTAÇÃO ---
        if bilhete_completo: # Verifica se há pelo menos um jogo gerado
            # Formata o dinheiro no estilo PT/BR (ex: 1.050,00)
            custo_formatado = f"R$ {custo_total:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
            
            texto_arquivo = f"--- SEU BILHETE COMPLETO: {args.suggest.upper()} ---\n"
            print("\n" + texto_arquivo.strip())
            
            for i, (dez_reais, jogo) in enumerate(bilhete_completo, 1):
                linha = f">> Jogo {i} ({dez_reais} dezenas): {jogo}"
                print(linha)
                texto_arquivo += linha + "\n"
                
            rodape = f"-------------------------\nCusto TOTAL estimado: {custo_formatado}\n-------------------------"
            print(rodape)
            texto_arquivo += rodape + "\n"
            
            salvar = input("\n-> Deseja guardar este bilhete num ficheiro de texto? (S/N): ")
            if salvar.strip().upper() == 'S':
                nome_arquivo = f"meus_jogos_{args.suggest}.txt"
                caminho = os.path.join(os.getcwd(), nome_arquivo)
                with open(caminho, 'w', encoding='utf-8') as f:
                    f.write(texto_arquivo)
                print(f"[V] Sucesso! O seu bilhete digital foi guardado em: {nome_arquivo}")
            
    elif args.check:
        conferir_apostas_pendentes()
        
    else:
        parser.print_help()

if __name__ == "__main__":
    main()