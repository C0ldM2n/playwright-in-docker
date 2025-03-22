import asyncio
import glob
import logging
import os
import zipfile

import requests
from playwright.async_api import BrowserContext, async_playwright

from config import settings

network_data = {
    "NTW_NAME": "Polygon zkEVM Cardona Testnet",
    "RPC_URL": "https://etherscan.cardona.zkevm-rpc.com/",
    "CHAIN_ID": "2442",
    "TICKER": "ETH",
    "EXPLORER": "https://cardona-zkevm.polygonscan.com",
}

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s",
    filename="logs.log",
    filemode="w",
)

logger = logging.getLogger(__name__)

console_handler = logging.StreamHandler()
logger.addHandler(console_handler)


def download_metamask_extension() -> str:
    """Downloads and extracts the MetaMask extension.

    Downloads the MetaMask extension from the official GitHub repository,
    extracts the ZIP archive, and returns the path to the extracted extension
    directory.  Uses the version specified in `settings.metamask_version`.

    Returns:
        str: The path to the extracted MetaMask extension directory.

    Raises:
        Exception: If the download fails (non-200 HTTP status code).
        requests.RequestException:  If there's a network problem during download.
        zipfile.BadZipFile: If the downloaded file is not a valid ZIP archive.
    """
    try:
        version = settings.METAMASK_VERSION
        url = f"https://github.com/MetaMask/metamask-extension/releases/download/v{version}/metamask-chrome-{version}.zip"
        local_zip = f"metamask-chrome-{version}.zip"
        extract_to = f"./extension/metamask-chrome-{version}"
        
        logger.info("Downloading MetaMask...")

        # Downloading MetaMask
        response = requests.get(url, stream=True)
        if response.status_code == 200:
            with open(local_zip, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            logger.info("Download finished.")
        else:
            raise Exception(f"Failed to download file: HTTP {response.status_code}.")
        
        # Creating MetaMask directory
        os.makedirs(extract_to, exist_ok=True)
        
        # Extracting zip
        with zipfile.ZipFile(local_zip, 'r') as zip_ref:
            zip_ref.extractall(extract_to)
        logger.info(f"MetaMask version {version} successfully installed!")
        
        os.remove(local_zip)

        return extract_to

    except requests.RequestException as e:
        logger.error(f"Error downloading MetaMask: {e}")
        raise
    except zipfile.BadZipFile as e:
        logger.error(f"Error extracting MetaMask zip file: {e}")
        raise

def find_metamask_extension() -> str:
    """Finds the MetaMask extension directory, downloading it if necessary.

    Searches for the MetaMask extension directory. If not found, it attempts
    to download and install the extension.

    Returns:
        str: The path to the MetaMask extension directory.
    """
    # Search extension manifest file
    extension_manifest_pattern = os.path.join("extension", "metamask-*", "manifest.json")
    if not glob.glob(extension_manifest_pattern):
        logger.error("MetaMask not found! Installing...")
        return download_metamask_extension()
    
    # Search extension directory
    extension_pattern = os.path.join("extension", "metamask-*")
    matches = glob.glob(extension_pattern)
    
    return matches[0]

async def create_wallet(context: BrowserContext) -> None:
    """Creates a new MetaMask wallet.

    Automates the process of creating a new MetaMask wallet, including
    accepting terms, setting a password, and recording the secret recovery
    phrase (for debugging purposes – handle with extreme care!).

    Args:
        context: The Playwright browser context.
    """
    # Waiting for MetaMask tab
    titles = [await p.title() for p in context.pages]
    while 'MetaMask' not in titles:
        titles = [await p.title() for p in context.pages]

    mm_page = context.pages[1]
    await mm_page.wait_for_load_state()

    # Agree to the terms of use and create a new wallet
    await mm_page.locator('//*[@id="onboarding__terms-checkbox"]').click()
    await mm_page.get_by_test_id(test_id='onboarding-create-wallet').click()
    
    # Refuse to collect information
    await mm_page.get_by_test_id(test_id='metametrics-no-thanks').click()
    
    # Enter the password
    await mm_page.get_by_test_id(test_id='create-password-new').fill(settings.PASSWORD)
    await mm_page.get_by_test_id(test_id='create-password-confirm').fill(settings.PASSWORD)
    
    await mm_page.get_by_test_id(test_id='create-password-terms').click()
    await mm_page.get_by_test_id(test_id='create-password-wallet').click()
    
    # Protect the wallet
    await mm_page.get_by_test_id(test_id='secure-wallet-recommended').click()
    
    # Show the secret phrase
    await mm_page.get_by_test_id(test_id='recovery-phrase-reveal').click()
    
    seed = []
    for i in range(12):
        seed.append(
            await mm_page.get_by_test_id(test_id=f'recovery-phrase-chip-{i}').inner_text()
        )

    logger.info("----------------------")
    logger.info("Secret phrase of this new wallet:")
    logger.info(" ".join(seed))
    logger.info(seed)

    await mm_page.get_by_test_id(test_id='recovery-phrase-next').click()
    
    # Seed phrase check
    await mm_page.get_by_test_id(test_id='recovery-phrase-input-2').click()

    await mm_page.get_by_test_id(test_id='recovery-phrase-input-2').fill(seed[2])
    await mm_page.get_by_test_id(test_id='recovery-phrase-input-3').fill(seed[3])
    await mm_page.get_by_test_id(test_id='recovery-phrase-input-7').fill(seed[7])

    # Click to "Confirm" button
    await mm_page.get_by_test_id(test_id='recovery-phrase-confirm').click()
    
    # Click to "Done" button
    await mm_page.get_by_test_id(test_id='onboarding-complete-done').click()
    
    # Click to "Next" button
    await mm_page.get_by_test_id(test_id='pin-extension-next').click()
    
    # Click to "Done" button
    await mm_page.get_by_test_id(test_id='pin-extension-done').click()
    
    logger.info("Wallet successfully created!")
    logger.info("----------------------")

async def add_network(context: BrowserContext) -> None:
    """Adds a custom network to MetaMask.

    Adds the network specified by the `network_data` global variable to
    the user's MetaMask wallet.

    Args:
        context: The Playwright browser context.
    """
    mm_page = context.pages[1]

    # Open network switch windows
    await mm_page.get_by_test_id(test_id='network-display').click()
    
    # Start adding a test network
    logger.info("----------------------")
    logger.info(f"Adding {network_data['NTW_NAME']} network in MetaMask...")
    logger.debug(f"{network_data}")
    
    await mm_page.locator('button:text("Add a custom network")').click()
    
    await mm_page.get_by_test_id(test_id='network-form-network-name').fill(network_data['NTW_NAME'])

    # Add custom RPC
    await mm_page.get_by_test_id(test_id='test-add-rpc-drop-down').click()
    await mm_page.locator('button:text("Add RPC URL")').click()

    await mm_page.get_by_test_id(test_id='rpc-url-input-test').fill(network_data['RPC_URL'])
    await mm_page.get_by_test_id(test_id='rpc-name-input-test').fill(network_data['NTW_NAME'])
    
    await mm_page.locator('button:text("Add URL")').click()
    
    # Enter the Chain ID and network currency symbol
    await mm_page.get_by_test_id(test_id='network-form-chain-id').fill(network_data['CHAIN_ID'])
    await mm_page.get_by_test_id(test_id='network-form-ticker-input').fill(network_data['TICKER'])

    # Enter the block explorer URL
    await mm_page.get_by_test_id(test_id='test-explorer-drop-down').click()
    await mm_page.locator('button:text("Add a block explorer URL")').click()

    await mm_page.get_by_test_id('explorer-url-input').fill(network_data['EXPLORER'])
    
    await mm_page.locator('button:text("Add URL")').click()
    
    # Saving new network
    await mm_page.locator('button:text("Save")').click()
    
    logger.info("Network successfully added!")
    logger.info("----------------------")

async def change_network(context: BrowserContext) -> None:
    """Changes the active network in MetaMask.

    Switches MetaMask to the network specified by the `network_data`
    global variable.

    Args:
        context: The Playwright browser context.
    """
    mm_page = context.pages[1]

    await mm_page.get_by_test_id(test_id='network-display').click()
    
    # Switching the network to new
    logger.info("----------------------")
    logger.info(f"Changing network to {network_data['NTW_NAME']}...")
    
    await mm_page.get_by_test_id(test_id=network_data['NTW_NAME']).click()

    logger.info("Network changed!")
    logger.info("----------------------")

async def run():
    """Runs the main automation script.

    Finds or installs the MetaMask extension, launches a persistent
    browser context, creates a new wallet, adds a custom network,
    and switches to that network.  The script keeps running until
    manually interrupted.
    """
    try:
        metamask_extension_path = find_metamask_extension()
    except FileNotFoundError as e:
        logger.info(f"Error: {e}")
        return
    
    async with async_playwright() as p:
        args = [
            '--disable-gpu',
            '--no-sandbox',
            '--disable-dev-shm-usage',
            f"--disable-extensions-except={metamask_extension_path}",
            f"--load-extension={metamask_extension_path}"
        ]

        context = await p.chromium.launch_persistent_context(
            user_data_dir='',
            headless=settings.HEADLESS,
            channel=settings.CHANNEL,
            args=args,
            ignore_https_errors=True,
            # slow_mo=700,
        )
        
        logger.info("----------------------")
        logger.info(f"CHANNEL: {settings.CHANNEL}")
        logger.info(f"HEADLESS: {settings.HEADLESS}")
        logger.info("----------------------")

        logger.info("Creating new wallet...")
        await create_wallet(context)

        logger.info("Adding new network in MetaMask...")
        await add_network(context)

        logger.info("Changing network...")
        await change_network(context)

        logger.info("Now you can use this browser, or exit with keyboard interrupt (CTRL + C).")

        # Open Codegen (UI Mode)
        # page = context.pages[1]
        # await page.pause()

        await asyncio.Future()


if __name__ == '__main__':
    try:
        asyncio.run(run())
    except KeyboardInterrupt:
        logger.info("Interrupted!")
        logger.info("Exiting the program.")
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")
        logger.info("Exiting the program.")
