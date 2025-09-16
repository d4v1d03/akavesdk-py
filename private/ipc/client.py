import time
import threading
from dataclasses import dataclass
from typing import Optional, List, Dict, Any, Union, NamedTuple
from web3 import Web3
from web3.middleware.proof_of_authority import ExtraDataToPOAMiddleware
from web3.exceptions import TransactionNotFound
from eth_account import Account
from eth_account.signers.local import LocalAccount
from .contracts import StorageContract, AccessManagerContract
from .ipc import StorageData, sign_block

@dataclass
class Config:
    dial_uri: str = ""
    private_key: str = ""
    storage_contract_address: str = ""
    access_contract_address: str = ""
    policy_factory_contract_address: str = ""

    @staticmethod
    def default_config() -> 'Config':
        return Config()


@dataclass 
class ContractsAddresses:
    storage: str = ""
    access_manager: str = ""
    policy_factory: str = ""


class BatchReceiptRequest(NamedTuple):
    hash: str
    key: str


class BatchReceiptResponse(NamedTuple):
    receipt: Optional[dict]
    error: Optional[Exception]
    key: str


@dataclass
class BatchReceiptResult:
    responses: List[BatchReceiptResponse]


class TransactionFailedError(Exception):
    pass


class Client:    
    def __init__(self, web3: Web3, auth: LocalAccount, storage: StorageContract, 
                 access_manager: Optional[AccessManagerContract] = None,
                 policy_factory: Optional[object] = None, 
                 list_policy_abi: Optional[dict] = None,
                 policy_factory_abi: Optional[dict] = None,
                 addresses: Optional[ContractsAddresses] = None,
                 chain_id: Optional[int] = None):
        self.storage = storage
        self.access_manager = access_manager
        self.policy_factory = policy_factory
        self.list_policy_abi = list_policy_abi
        self.policy_factory_abi = policy_factory_abi
        self.auth = auth
        self.eth = web3
        self.addresses = addresses or ContractsAddresses()
        self._chain_id = chain_id

    @classmethod
    def dial(cls, config: Config) -> 'Client':
        try:
            client = Web3(Web3.HTTPProvider(config.dial_uri))
            if not client.is_connected():
                raise ConnectionError(f"Failed to connect to {config.dial_uri}")
        except Exception as e:
            raise ConnectionError(f"Failed to connect to {config.dial_uri}: {e}")

        client.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)

        try:
            private_key = config.private_key
            if private_key.startswith('0x'):
                private_key = private_key[2:]
            account = Account.from_key(private_key)
        except Exception as e:
            raise ValueError(f"Failed to load private key: {e}")

        try:
            chain_id = client.eth.chain_id
        except Exception as e:
            raise ConnectionError(f"Failed to get chain ID: {e}")

        storage = StorageContract(client, config.storage_contract_address)
        
        access_manager = None
        if config.access_contract_address:
            access_manager = AccessManagerContract(client, config.access_contract_address)

        policy_factory = None
        list_policy_abi = None
        policy_factory_abi = None
        if config.policy_factory_contract_address:
            try:
                from .contracts import PolicyFactoryContract, ListPolicyMetaData, PolicyFactoryMetaData
                policy_factory = PolicyFactoryContract(client, config.policy_factory_contract_address)
                list_policy_abi = ListPolicyMetaData.ABI
                policy_factory_abi = PolicyFactoryMetaData.ABI
            except ImportError:
                pass  
        
        addresses = ContractsAddresses(
            storage=config.storage_contract_address,
            access_manager=config.access_contract_address,
            policy_factory=config.policy_factory_contract_address
        )

        ipc_client = cls(
            web3=client,
            auth=account,
            storage=storage, 
            access_manager=access_manager,
            policy_factory=policy_factory,
            list_policy_abi=list_policy_abi,
            policy_factory_abi=policy_factory_abi,
            addresses=addresses,
            chain_id=chain_id
        )

        return ipc_client

    @classmethod
    def deploy_contracts(cls, config: Config) -> 'Client':
        eth_client = Web3(Web3.HTTPProvider(config.dial_uri))
        if not eth_client.is_connected():
            raise ConnectionError(f"Failed to connect to {config.dial_uri}")

        # Setup account
        private_key = config.private_key
        if private_key.startswith('0x'):
            private_key = private_key[2:]
        account = Account.from_key(private_key)
        
        chain_id = eth_client.eth.chain_id
        
        client = cls(
            web3=eth_client,
            auth=account,
            storage=None,  
            chain_id=chain_id
        )
        
        try:
            from .contracts import (
                deploy_erc1967_proxy, deploy_access_manager, deploy_list_policy, 
                deploy_policy_factory, StorageContract, AccessManagerContract, 
                PolicyFactoryContract, ListPolicyMetaData, PolicyFactoryMetaData
            )
            
            try:
                from .contracts import deploy_akave_token, deploy_storage
            except ImportError:
                raise NotImplementedError(
                    "AkaveToken and Storage deployment functions are not yet implemented. "
                    "The following functions are missing: deploy_akave_token, deploy_storage"
                )
            
            akave_token_addr, tx_hash, token_contract = deploy_akave_token(eth_client, account)
            client.wait_for_tx(tx_hash)
            
            storage_impl_addr, tx_hash, _ = deploy_storage(eth_client, account)
            client.wait_for_tx(tx_hash)
            
            storage_abi = StorageContract.get_abi()
            init_data = StorageContract.encode_function_data("initialize", [akave_token_addr])
            
            storage_proxy_addr, tx_hash, _ = deploy_erc1967_proxy(
                eth_client, account, storage_impl_addr, init_data
            )
            client.wait_for_tx(tx_hash)
            
            storage = StorageContract(eth_client, storage_proxy_addr)
            client.storage = storage
            client.addresses.storage = storage_proxy_addr
            
            minter_role = token_contract.functions.MINTER_ROLE().call()
            tx_hash = token_contract.functions.grantRole(minter_role, storage_proxy_addr).transact({
                'from': account.address
            })
            client.wait_for_tx(tx_hash)
            
            access_addr, tx_hash, access_manager = deploy_access_manager(eth_client, account, storage_proxy_addr)
            client.wait_for_tx(tx_hash)
            
            client.access_manager = access_manager
            client.addresses.access_manager = access_addr
            
            tx_hash = storage.set_access_manager(account, access_addr)
            client.wait_for_tx(tx_hash)
            
            base_list_policy_addr, tx_hash, _ = deploy_list_policy(eth_client, account)
            client.wait_for_tx(tx_hash)
            
            policy_factory_addr, tx_hash, policy_factory = deploy_policy_factory(
                eth_client, account, base_list_policy_addr
            )
            client.wait_for_tx(tx_hash)
            
            client.policy_factory = policy_factory
            client.addresses.policy_factory = policy_factory_addr
            
            client.list_policy_abi = ListPolicyMetaData.ABI
            client.policy_factory_abi = PolicyFactoryMetaData.ABI
            
            return client
            
        except ImportError as e:
            raise NotImplementedError(
                f"Contract deployment functions not available: {e}. "
                "This feature requires complete contract bindings."
            )

    def chain_id(self) -> int:
        return self._chain_id

    def deploy_list_policy(self, user_address: str) -> str:
        if not self.policy_factory or not self.list_policy_abi:
            raise ValueError("PolicyFactory or ListPolicy ABI not available")
        
        list_policy_contract = self.eth.eth.contract(abi=self.list_policy_abi)
        abi_bytes = list_policy_contract.encodeABI(fn_name='initialize', args=[user_address])
        
        tx_hash = self.policy_factory.deploy_policy(self.auth, bytes.fromhex(abi_bytes[2:]))
        receipt = self.wait_for_tx(tx_hash)
        
        if not self.policy_factory_abi:
            raise ValueError("PolicyFactory ABI not available")
            
        policy_deployed_event = None
        for item in self.policy_factory_abi:
            if item.get('type') == 'event' and item.get('name') == 'PolicyDeployed':
                policy_deployed_event = item
                break
        
        if not policy_deployed_event:
            raise ValueError("PolicyDeployed event not found in ABI")
        
        event_hash = self.eth.keccak(text=f"PolicyDeployed({','.join([input['type'] for input in policy_deployed_event['inputs']])})")
        
        policy_instance_address = None
        for log in receipt.logs:
            if len(log.topics) >= 3 and log.topics[0] == event_hash:
                policy_instance_address = Web3.to_checksum_address('0x' + log.topics[2].hex()[-40:])
                break
        
        if not policy_instance_address:
            raise RuntimeError("Failed to extract policy instance address from deployment transaction")
        
        from .contracts import ListPolicyContract
        return ListPolicyContract(self.eth, policy_instance_address)

    def get_transaction_receipts_batch(self, requests: List[BatchReceiptRequest], 
                                     timeout: float = 30.0) -> BatchReceiptResult:
        try:
            batch_requests = []
            for req in requests:
                batch_requests.append(('eth_getTransactionReceipt', [req.hash]))
            
            raw_responses = self.eth.manager.request_blocking_batch(batch_requests)
            
            responses = []
            for i, (req, raw_response) in enumerate(zip(requests, raw_responses)):
                response = BatchReceiptResponse(
                    receipt=raw_response.get('result') if raw_response.get('result') else None,
                    error=Exception(raw_response.get('error', {}).get('message', 'Unknown error')) if 'error' in raw_response else None,
                    key=req.key
                )
                responses.append(response)
            
            return BatchReceiptResult(responses=responses)
            
        except Exception as e:
            responses = []
            for req in requests:
                try:
                    receipt = self.eth.eth.get_transaction_receipt(req.hash)
                    response = BatchReceiptResponse(receipt=dict(receipt), error=None, key=req.key)
                except TransactionNotFound:
                    response = BatchReceiptResponse(receipt=None, error=None, key=req.key)
                except Exception as err:
                    response = BatchReceiptResponse(receipt=None, error=err, key=req.key)
                responses.append(response)
            
            return BatchReceiptResult(responses=responses)

    def wait_for_tx(self, tx_hash: Union[str, bytes], timeout: float = 120.0) -> dict:
        if isinstance(tx_hash, bytes):
            tx_hash = tx_hash.hex()
        if not tx_hash.startswith('0x'):
            tx_hash = '0x' + tx_hash

        try:
            receipt = self.eth.eth.get_transaction_receipt(tx_hash)
            if receipt.status == 1:
                return receipt
            else:
                raise TransactionFailedError("Transaction failed")
        except TransactionNotFound:
            pass  
        except Exception as e:
            raise TransactionFailedError(f"Error checking transaction receipt: {e}")
        
        start_time = time.time()
        poll_interval = 0.2  
        
        while True:
            current_time = time.time()
            if current_time - start_time > timeout:
                raise TimeoutError(f"Timeout waiting for transaction {tx_hash}")
            
            try:
                receipt = self.eth.eth.get_transaction_receipt(tx_hash)
                if receipt.status == 1:
                    return receipt
                else:
                    raise TransactionFailedError("Transaction failed")
            except TransactionNotFound:
                time.sleep(poll_interval)
                continue
            except Exception as e:
                raise TransactionFailedError(f"Error checking transaction receipt: {e}")