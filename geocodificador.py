import pandas as pd
import googlemaps
import time

# 1. COLOQUE SUA CHAVE AQUI
CHAVE_API = "AIzaSyDpu3q-czcdAU905z9wQ0kLmJ0y9puS2Bc"
gmaps = googlemaps.Client(key=CHAVE_API)

def atualizar_coordenadas():
    arquivo = "lista_clientes_formatada.xlsx"
    print("Iniciando motor do Google Maps...")
    
    try:
        df = pd.read_excel(arquivo)
    except FileNotFoundError:
        print(f"Erro: Arquivo '{arquivo}' não encontrado.")
        return

    if 'Latitude' not in df.columns: df['Latitude'] = None
    if 'Longitude' not in df.columns: df['Longitude'] = None

    novos_pontos = 0

    for index, row in df.iterrows():
        if pd.isna(row['Latitude']) or pd.isna(row['Longitude']):
            cep = str(row['CEP']).strip()
            if cep and cep != 'nan':
                try:
                    # O Google processa a busca de forma inteligente
                    resultado = gmaps.geocode(f"{cep}, Brasil")
                    
                    if resultado:
                        lat = resultado[0]['geometry']['location']['lat']
                        lng = resultado[0]['geometry']['location']['lng']
                        df.at[index, 'Latitude'] = lat
                        df.at[index, 'Longitude'] = lng
                        novos_pontos += 1
                        print(f"✅ Encontrado: {row['Razão Social']} -> {lat}, {lng}")
                    else:
                        print(f"❌ Não encontrado: CEP {cep} - {row['Razão Social']}")
                    
                    time.sleep(0.1) # Pausa muito menor, o Google é rápido
                except Exception as e:
                    print(f"Erro na API ao buscar {cep}: {e}")

    if novos_pontos > 0:
        df.to_excel(arquivo, index=False)
        print(f"\nSucesso! {novos_pontos} locais atualizados na planilha usando o Google.")
    else:
        print("\nBase 100% atualizada! Nenhum CEP pendente.")

if __name__ == "__main__":
    atualizar_coordenadas()