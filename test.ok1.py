from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

driver = webdriver.Remote(
    command_executor='http://localhost:4444/wd/hub',  # Cambia la URL según tu Grid
    options=webdriver.ChromeOptions()
)

driver.get("https://www.digimobil.es/movil/")

try:
    # Intentar encontrar el botón de aceptar cookies
    try:
        aceptar_cookies = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Aceptar todas las cookies')]"))
        )
        aceptar_cookies.click()
        print("Cookies aceptadas")
    except:
        print("No se encontró el botón de aceptar cookies, continuando con la búsqueda de 'LO QUIERO'")

    # Buscar todos los elementos que contienen el texto 'LO QUIERO'
    elementos_lo_quiero = driver.find_elements(By.XPATH, "//*[contains(text(), 'LO QUIERO')]")

    # Imprimir la cantidad de elementos encontrados y sus etiquetas HTML
    if elementos_lo_quiero:
        print(f"Se encontraron {len(elementos_lo_quiero)} elementos con el texto 'LO QUIERO':")
        for elemento in elementos_lo_quiero:
            print(elemento.tag_name, ":", elemento.get_attribute('outerHTML'))
    else:
        print("No se encontraron elementos con el texto 'LO QUIERO'.")

except Exception as e:
    print(f"Hubo un error al interactuar con la página: {e}")

# Cierra el navegador al finalizar
driver.quit()

