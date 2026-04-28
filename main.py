import argparse
import os
import sys

# Importações dos módulos internos do projeto
from src.database import inicializar_bd
from src.collector import atualizar_resultados
from src.analyzer import obter_estatisticas_completas
from src.generator import sugerir_jogo, calcular_custo_jogos
from src.checker import conferir_resultados

def main():
    # Garante que o banco de dados e as tabelas existam antes de qualquer operação
    inicializar_bd()

    parser = argparse.ArgumentParser(description="Agente de IA - Analista de Loterias (Interface CLI)")
    parser.add_argument("--update", choices=['megasena', 'lotofacil', 'quina'], help="Sincroniza os últimos resultados da loteria escolhida")
    parser.add_argument("--suggest", choices=['megasena', 'lotofacil', 'quina'], help="Gera sugestões de apostas no terminal")
    parser.add_argument("--check", action="store_true", help="Confere as apostas salvas contra os resultados oficiais")

    args = parser.parse_args()

    if args.update:
        print(f"[*] Iniciando atualização para {args.update.upper()}...")
        atualizar_resultados(args.update)
        print("[V] Sincronização concluída.")
        
    elif args.suggest:
        print(f"\n[*] Gerador de Bilhetes: {args.suggest.upper()}")
        
        bilhete_completo = []
        custo_total = 0.0
        
        while True:
            try:
                entrada_jogos = input("\n-> Quantos jogos deseja gerar? (Padrão: 1): ")
                qtd_jogos = int(entrada_jogos) if entrada_jogos.strip() else 1
                
                entrada_dezenas = input(f"-> Quantas dezenas por jogo? (Pressione Enter para o mínimo): ")
                qtd_dezenas = int(entrada_dezenas) if entrada_dezenas.strip() else None
                
                jogos_lote = sugerir_jogo(args.suggest, qtd_jogos, qtd_dezenas)
                
                if isinstance(jogos_lote, str):
                    print(f"[!] Erro: {jogos_lote}")
                else:
                    dezenas_reais = len(jogos_lote[0])
                    custo_lote = calcular_custo_jogos(args.suggest, qtd_jogos, dezenas_reais)
                    custo_total += custo_lote
                    
                    for jogo in jogos_lote:
                        bilhete_completo.append((dezenas_reais, jogo))
                        
                    print(f"[V] {qtd_jogos} jogo(s) de {dezenas_reais} dezenas adicionado(s)!")

            except ValueError:
                print("[!] Erro: Digite apenas números válidos.")
                continue
                
            continuar = input("\n-> Deseja gerar MAIS apostas para este bilhete? (S/N): ")
            if continuar.strip().upper() != 'S':
                break
        
        if bilhete_completo:
            print(f"\n--- SEU BILHETE: {args.suggest.upper()} ---")
            for i, (dez, jogo) in enumerate(bilhete_completo, 1):
                print(f">> Jogo {i} ({dez} dezenas): {jogo}")
                
            print(f"-------------------------")
            print(f"Custo TOTAL estimado: R$ {custo_total:,.2f}")
            print(f"-------------------------")
            
            salvar = input("\n-> Deseja salvar este bilhete em um arquivo .txt? (S/N): ")
            if salvar.strip().upper() == 'S':
                nome_arq = f"meus_jogos_{args.suggest}.txt"
                with open(nome_arq, 'w', encoding='utf-8') as f:
                    f.write(f"Bilhete {args.suggest.upper()}\n")
                    for _, j in bilhete_completo: f.write(f"{j}\n")
                print(f"[V] Salvo em: {nome_arq}")
            
    elif args.check:
        print("[*] Conferindo resultados oficiais...")
        # A lógica aqui busca as modalidades cadastradas
        for lot in ['megasena', 'lotofacil', 'quina']:
            res = conferir_resultados(lot)
            if res is not None and not res.empty:
                print(f"\n--- Resultados para {lot.upper()} ---")
                print(res.to_string(index=False))
        
    else:
        parser.print_help()

if __name__ == "__main__":
    main()