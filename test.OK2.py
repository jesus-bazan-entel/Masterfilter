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
    # Intentar encontrar y hacer clic en el botón de aceptar o rechazar cookies
    try:
        aceptar_cookies = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Aceptar todas las cookies')]"))
        )
        aceptar_cookies.click()
        print("Cookies aceptadas")
    except:
        try:
            rechazar_cookies = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Rechazar todas')]"))
            )
            rechazar_cookies.click()
            print("Cookies rechazadas")
        except:
            print("No se encontró el botón de aceptar o rechazar cookies, eliminando overlay de cookies")

    # Ejecutar un script para eliminar el overlay si sigue existiendo
    driver.execute_script("""
        var overlay = document.getElementById('CybotCookiebotDialogBodyUnderlay');
        if (overlay) {
            overlay.parentNode.removeChild(overlay);
        }
    """)

    # Buscar todos los elementos que contienen el texto 'LO QUIERO'
    elementos_lo_quiero = driver.find_elements(By.XPATH, "//*[contains(text(), 'LO QUIERO')]")

    # Imprimir la cantidad de elementos encontrados y sus etiquetas HTML
    if elementos_lo_quiero:
        print(f"Se encontraron {len(elementos_lo_quiero)} elementos con el texto 'LO QUIERO':")
        for elemento in elementos_lo_quiero:
            print(elemento.tag_name, ":", elemento.get_attribute('outerHTML'))
        
        # Hacer clic en el primer elemento con el texto 'LO QUIERO'
        primer_elemento_lo_quiero = elementos_lo_quiero[0]

        # Esperar hasta que el elemento esté realmente clicable
        WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, "//*[contains(text(), 'LO QUIERO')]")))

        primer_elemento_lo_quiero.click()
        print("Clic en el primer enlace 'LO QUIERO'")
        
        # Esperar hasta que la nueva página esté completamente cargada
        WebDriverWait(driver, 20).until(lambda d: d.execute_script('return document.readyState') == 'complete')

        # Imprimir el HTML de la página final
        print("HTML de la página final después del clic:")
        print(driver.page_source)

    else:
        print("No se encontraron elementos con el texto 'LO QUIERO'.")

except Exception as e:
    print(f"Hubo un error al interactuar con la página: {e}")

# Cierra el navegador al finalizar
driver.quit()

