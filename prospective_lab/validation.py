"""Pure read-only evidence decoders. No network, wallets, or transaction construction.
Layouts checked against pump-public-docs idl/pump.json blob
2f1c65d4ff209d0f233c0e95552dd82873e4afb5 and PUMP_SWAP_README.md.
"""
from __future__ import annotations
import base64
import hashlib
import re
import struct

PUMP = '6EF8rrecthR5Dkzon8Nwu78hRvfCKubJ14M5uBEwF6P'
AMM = 'pAMMBay6oceH9fJKBRHGP5D4bD4sWpmSwMn52FMfXEA'
GLOBAL = '4wTV1YmiEkRvAtNtsSGPtUrqRYQMe5SKy2uB4Jjaxnjf'
WSOL = 'So11111111111111111111111111111111111111112'
TOKEN = 'TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA'
TOKEN22 = 'TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb'
ZERO = '11111111111111111111111111111111'
ALPHABET = '123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz'
MIGRATE = bytes([155,234,231,146,236,158,162,30])
MIGRATE_V2 = bytes([187,203,18,31,206,237,254,41])
COMPLETE = hashlib.sha256(b'event:CompletePumpAmmMigrationEvent').digest()[:8]
CREATE_POOL = hashlib.sha256(b'global:create_pool').digest()[:8]
EVENT_CPI = bytes([228,69,165,46,81,203,154,29])
SCHEMA = 'migration-evidence-v1'


def b58(data: bytes) -> str:
    n, out = int.from_bytes(data, 'big'), ''
    while n:
        n, r = divmod(n, 58)
        out = ALPHABET[r] + out
    return '1' * (len(data) - len(data.lstrip(b'\0'))) + out


def un58(value: str) -> bytes:
    if not isinstance(value, str) or len(value) > 20000:
        raise ValueError('invalid_base58')
    n = 0
    for c in value:
        n = n * 58 + ALPHABET.index(c)
    return b'\0' * (len(value) - len(value.lstrip('1'))) + n.to_bytes((n.bit_length()+7)//8, 'big')


def pubkey(value) -> bool:
    try:
        return isinstance(value, str) and len(un58(value)) == 32
    except (ValueError, TypeError):
        return False


def account_bytes(account, owner, minimum):
    if not isinstance(account, dict) or account.get('owner') not in owner or account.get('executable') is not False:
        raise ValueError('account_owner_or_executable')
    data = account.get('data')
    if not isinstance(data, list) or len(data) != 2 or data[1] != 'base64':
        raise ValueError('account_encoding')
    raw = base64.b64decode(data[0], validate=True)
    if len(raw) < minimum:
        raise ValueError('account_layout_short')
    return raw


def migration_index(result):
    raw = account_bytes((result or {}).get('value'), {PUMP}, 145)
    if raw[:8] != hashlib.sha256(b'account:Global').digest()[:8] or raw[8] != 1:
        raise ValueError('global_layout')
    address = b58(raw[113:145])
    if address in {ZERO, PUMP, AMM}:
        raise ValueError('invalid_migration_index')
    return address


def instruction_groups(tx):
    message = ((tx or {}).get('transaction') or {}).get('message') or {}
    top = message.get('instructions') or []
    inner = {g['index']: g.get('instructions') or [] for g in (tx.get('meta') or {}).get('innerInstructions') or []}
    for index, ins in enumerate(top):
        yield index, [ins] + inner.get(index, [])


def decode_event(raw):
    # Legacy 168-byte event and the append-only quote_mint extension are supported.
    if len(raw) not in (168, 200) or raw[:8] != COMPLETE:
        return None
    return {'mint': b58(raw[40:72]), 'mint_amount_raw': str(struct.unpack_from('<Q', raw,72)[0]),
            'quote_amount_raw': str(struct.unpack_from('<Q', raw,80)[0]),
            'bonding_curve': b58(raw[96:128]), 'timestamp': struct.unpack_from('<q',raw,128)[0],
            'pool': b58(raw[136:168]), 'quote_mint': b58(raw[168:200]) if len(raw)==200 else WSOL,
            'event_base64': base64.b64encode(raw).decode()}


def attributed_events(tx):
    events, stack = [], []
    for line in (tx.get('meta') or {}).get('logMessages') or []:
        if not isinstance(line, str):
            continue
        invoke = re.fullmatch(r'Program ([1-9A-HJ-NP-Za-km-z]+) invoke \[(\d+)\]', line)
        done = re.fullmatch(r'Program ([1-9A-HJ-NP-Za-km-z]+) (success|failed:.*)', line)
        if invoke:
            depth = int(invoke[2])
            if depth != len(stack) + 1:
                stack = []
            stack.append(invoke[1])
        elif done:
            if stack and stack[-1] == done[1]:
                stack.pop()
            else:
                stack = []
        elif line.startswith('Program data: ') and stack and stack[-1] == PUMP:
            try:
                event = decode_event(base64.b64decode(line[14:], validate=True))
                if event:
                    events.append(event)
            except (ValueError, TypeError):
                pass
    # Anchor emit_cpi: require a self-CPI whose recorded parent is Pump.
    for _, group in instruction_groups(tx):
        ancestors = {}
        for i, ins in enumerate(group):
            depth = 1 if i == 0 else ins.get('stackHeight')
            if not isinstance(depth, int):
                continue
            parent = ancestors.get(depth-1)
            ancestors = {d:p for d,p in ancestors.items() if d < depth}
            ancestors[depth] = ins.get('programId')
            if parent != PUMP or ins.get('programId') != PUMP:
                continue
            try:
                raw = un58(ins.get('data', ''))
                event = decode_event(raw[8:]) if raw[:8] == EVENT_CPI else None
                if event:
                    events.append(event)
            except (ValueError, TypeError):
                pass
    return events


def audit_migrations(tx):
    if not isinstance(tx, dict) or not isinstance(tx.get('meta'), dict) or tx['meta'].get('err') is not None:
        return []
    events, results, used = attributed_events(tx), [], set()
    for index, group in instruction_groups(tx):
        for ins in group:
            try:
                discriminator = un58(ins.get('data',''))
                if ins.get('programId') != PUMP or discriminator not in {MIGRATE,MIGRATE_V2}:
                    continue
                accounts = [a.get('pubkey','') if isinstance(a,dict) else a for a in ins.get('accounts') or []]
                is_v2 = discriminator == MIGRATE_V2
                curve_index, amm_index, pool_index = (4,9,10) if is_v2 else (3,8,9)
                if len(accounts)<=pool_index or accounts[amm_index]!=AMM or not all(pubkey(accounts[i]) for i in (2,curve_index,pool_index)):
                    continue
                if is_v2 and accounts[3]!=WSOL:
                    continue  # Preserve the original SOL-paired migration universe.
                mint, curve, pool = accounts[2], accounts[curve_index], accounts[pool_index]
                if (mint,pool) in used:
                    continue
                used.add((mint,pool))
                matches = [e for e in events if e['mint']==mint and e['pool']==pool and e['bonding_curve']==curve
                           and e['quote_mint'] in {WSOL,ZERO} and int(e['mint_amount_raw'])>0 and int(e['quote_amount_raw'])>0]
                creates = []
                for child in group:
                    try:
                        ac = child.get('accounts') or []
                        if (child.get('programId')==AMM and un58(child.get('data',''))[:8]==CREATE_POOL
                                and all(key in ac for key in (pool,mint,WSOL))):
                            creates.append({'programId':AMM,'accounts':ac,'data':child['data']})
                    except (ValueError,TypeError):
                        pass
                message = (tx.get('transaction') or {}).get('message') or {}
                keys = [a.get('pubkey','') if isinstance(a,dict) else a for a in message.get('accountKeys') or []]
                pre = post = None
                if pool in keys:
                    k = keys.index(pool)
                    before, after = tx['meta'].get('preBalances') or [], tx['meta'].get('postBalances') or []
                    if k<len(before) and k<len(after):
                        pre, post = before[k], after[k]
                funded_new = type(pre) is int and type(post) is int and pre==0 and post>0
                status = 'confirmed_new_migration' if matches and creates and funded_new else 'unresolved_no_new_migration_evidence'
                results.append({'schema':SCHEMA,'status':status,'mint':mint,'pool':pool,'quote_mint':WSOL,
                    'instruction_index':index,'instruction_version':'migrate_v2' if is_v2 else 'migrate','curve':curve,'event':matches[0] if matches else None,
                    'pool_creation_instructions':creates,'pool_pre_lamports':pre,'pool_post_lamports':post,'new_pool_funding_proven':funded_new,'chain_slot':tx.get('slot'),'chain_block_time':tx.get('blockTime'),
                    'evidence_note':'Matching Pump event, PumpSwap create_pool, and zero-to-positive pool funding required; absent evidence or prefunded pools remain unresolved.'})
            except (ValueError,TypeError,KeyError):
                continue
    return results


def pool_layout(account):
    raw = account_bytes(account, {AMM}, 211)
    if raw[:8] != hashlib.sha256(b'account:Pool').digest()[:8]:
        raise ValueError('pool_discriminator')
    return {'base_mint':b58(raw[43:75]),'quote_mint':b58(raw[75:107]),
            'base_vault':b58(raw[139:171]),'quote_vault':b58(raw[171:203]),
            'virtual_quote_reserves_raw':str(int.from_bytes(raw[245:261],'little',signed=True)) if len(raw)>=261 else '0',
            'pool_data_base64':base64.b64encode(raw).decode()}


def mint_layout(account):
    raw = account_bytes(account, {TOKEN,TOKEN22}, 82)
    if raw[45] != 1:
        raise ValueError('mint_not_initialized')
    return {'supply_raw':str(int.from_bytes(raw[36:44],'little')),'decimals':raw[44],
        'token_program':account['owner'],'freeze_authority_present':int.from_bytes(raw[46:50],'little')!=0,
        'extensions_fully_validated':account['owner']==TOKEN and len(raw)==82}


def vault_layout(account, mint, pool):
    raw = account_bytes(account, {TOKEN,TOKEN22}, 165)
    if b58(raw[:32])!=mint or b58(raw[32:64])!=pool or raw[108]!=1:
        raise ValueError('vault_mint_authority_or_state')
    return {'amount_raw':str(int.from_bytes(raw[64:72],'little')),'token_program':account['owner'],
            'extensions_fully_validated':account['owner']==TOKEN and len(raw)==165}
