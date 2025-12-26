from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
import time

chrome_options = Options()
# Deshabilitar la detección de automatización
chrome_options.add_experimental_option(
    'excludeSwitches', ['enable-automation'])
chrome_options.add_experimental_option('useAutomationExtension', False)

# Cambiar el user-agent para parecer un navegador real
chrome_options.add_argument(
    '--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36')

# Ocultar el hecho de que estamos utilizando un WebDriver
chrome_options.add_argument('--disable-blink-features=AutomationControlled')

# Maximizar la ventana para simular un navegador normal
chrome_options.add_argument('--start-maximized')

# Desactivar WebRTC para evitar la fuga de IP real
chrome_options.add_argument('--disable-webrtc')

# Activar el modo de incógnito
chrome_options.add_argument('--incognito')

# Habilitar el uso de WebGL y aceleración de hardware
chrome_options.add_argument('--enable-webgl')
chrome_options.add_argument('--enable-accelerated-2d-canvas')
chrome_options.add_argument('--disable-gpu')

# Configurar para que no muestre las notificaciones del navegador
chrome_options.add_argument('--disable-notifications')

# Configurar para evitar la carga de imágenes y hacer que el navegador sea más ligero
chrome_options.add_argument('--blink-settings=imagesEnabled=false')

chrome_options.add_argument('--headless')
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--disable-dev-shm-usage')
# Algunas versiones de Chrome requieren esto para headless
chrome_options.add_argument('--disable-gpu')
# Tamaño de la ventana, puede mejorar la estabilidad
chrome_options.add_argument('--window-size=1920x1080')
# Deshabilita el rasterizador de software
chrome_options.add_argument('--disable-software-rasterizer')

driver = webdriver.Remote(
    command_executor='http://172.19.0.2:4444/wd/hub',
    options=chrome_options
)


try:
    driver.get("https://www.digimobil.es/movil/")

    # Ejecutar un script para eliminar el overlay si sigue existiendo
    driver.execute_script("""
        var overlay = document.getElementById('CybotCookiebotDialogBodyUnderlay');
        if (overlay) {
            overlay.parentNode.removeChild(overlay);
        }
    """)

    #link = driver.find_element(By.ID, "loquiero_/combina-telefonia-internet/?movil=1495")
    #actions = ActionChains(driver)
    #actions.move_to_element(link).click().perform()

    link = driver.find_element(By.ID, "loquiero_/combina-telefonia-internet/?movil=1495")
    time.sleep(5)
    driver.execute_script("arguments[0].click();", link)
    #driver.implicitly_wait(10)  # Puedes ajustar el tiempo según el contenido de la página
    time.sleep(5)
    html = driver.page_source
    print(html)

        # Hacer clic en el primer elemento con el texto 'LO QUIERO'
        #link.click()

        # Esperar hasta que el elemento esté realmente clicable
        #WebDriverWait(driver, 20).until(EC.element_to_be_clickable(
        #    (By.XPATH, "//*[contains(text(), 'LO QUIERO')]")))

        #primer_elemento_lo_quiero.click()
        #print("Clic en el primer enlace 'LO QUIERO'")

        # Esperar hasta que la nueva página esté completamente cargada
        #WebDriverWait(driver, 20).until(lambda d: d.execute_script(
        #    'return document.readyState') == 'complete')

        # Ejecutar un script para eliminar el overlay si sigue existiendo
        # driver.execute_script("""
        #    var overlay = document.getElementById('CybotCookiebotDialogBodyUnderlay');
        #    if (overlay) {
        #        overlay.parentNode.removeChild(overlay);
        #    }
        # """)

        # Imprimir el HTML del elemento que contiene 'LO QUIERO' en la página final
        # elemento_final = WebDriverWait(driver, 10).until(
        #    EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'LO QUIERO')]"))
        # )
        # print("Elemento con el texto 'LO QUIERO' en la página final:")
        # print(elemento_final.get_attribute('outerHTML'))

except Exception as e:
    print(f"Hubo un error al interactuar con la página: {e}")

# Cierra el navegador al finalizar
driver.quit()
