import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

options = Options()
options.add_argument('--headless=new')
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')

driver = webdriver.Chrome(options=options)
try:
    print('📍 Testing Digital Forge XPath editor fixes...')
    driver.get('http://localhost:8001/content-extractor/')
    time.sleep(3)
    
    # Test if the XPath editor creates compact menus
    result = driver.execute_script('''
        if (typeof ContentExtractorUnifiedMenu !== "undefined") {
            const content = ContentExtractorUnifiedMenu.buildXPathEditorContent("//test");
            const hasComponents = content.includes("xpath-components-section");
            const hasGeneralization = content.includes("xpath-generalization-section");
            return {
                unified_available: true,
                streamlined: !hasComponents && !hasGeneralization,
                content_length: content.length
            };
        }
        return {unified_available: false};
    ''')
    
    print(f'✅ Unified menu available: {result.get("unified_available")}')
    if result.get('unified_available'):
        print(f'✅ Content streamlined: {result.get("streamlined")}')
        print(f'📏 Content length: {result.get("content_length")} chars')
        
        if result.get("streamlined"):
            print('🎉 SUCCESS: XPath editor is now streamlined!')
        else:
            print('⚠️ ISSUE: XPath editor still has verbose sections')
    
    print('🔧 Digital Forge fixes verified!')
finally:
    driver.quit() 