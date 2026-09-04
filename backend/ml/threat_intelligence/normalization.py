"""Deterministic canonicalization and defanging routines for technical threat indicators."""
from __future__ import annotations

import hashlib
import ipaddress
import re
from typing import Optional, Tuple
from urllib.parse import urlparse, urlunparse

from .config import IOCType


def defang_text(val: str) -> str:
    """Removes common security defanging conventions (e.g. hxxp, [.], [dot])."""
    if not val:
        return ""
    text = val.strip()
    text = re.sub(r'\[\.\]', '.', text)
    text = re.sub(r'\(dot\)', '.', text, flags=re.IGNORECASE)
    text = re.sub(r'\[dot\]', '.', text, flags=re.IGNORECASE)
    text = re.sub(r'\[\:\]', ':', text)
    text = re.sub(r'^hxxps?:\/\/', lambda m: 'https://' if 's' in m.group(0).lower() else 'http://', text, flags=re.IGNORECASE)
    return text


def canonicalize_ipv4(val: str) -> str:
    """
    Deterministically normalizes an IPv4 address string.
    
    Transforms:
      - Defangs '[.]' and whitespace
      - Validates RFC 791 syntax
      - Returns canonical dotted-quad string without leading zeros (e.g. '103.145.22.18')
    """
    clean = defang_text(val).replace(" ", "")
    addr = ipaddress.IPv4Address(clean)
    return str(addr)


def canonicalize_ipv6(val: str) -> str:
    """
    Deterministically normalizes an IPv6 address string.
    
    Transforms:
      - Defangs '[:]' and whitespace
      - Validates RFC 4291 syntax
      - Returns standard RFC 5952 lowercase compressed format (e.g. '2001:db8::1')
    """
    clean = defang_text(val).replace(" ", "")
    addr = ipaddress.IPv6Address(clean)
    return addr.compressed.lower()


def canonicalize_domain(val: str) -> str:
    """
    Deterministically normalizes a domain name to an IDNA-canonical lowercase representation.
    
    Transforms:
      - Defangs '[.]' and whitespace
      - Strips accidental URL scheme prefixes (http://, https://)
      - Strips syntactic trailing dot (e.g. 'example.com.' -> 'example.com')
      - Normalizes Internationalized Domain Names (IDNA) so Unicode and Punycode forms are equivalent
      - Returns canonical lowercased ASCII/Punycode domain string
    """
    clean = defang_text(val).strip()
    # Remove protocol prefix if accidentally included
    clean = re.sub(r'^[a-zA-Z]+:\/\/', '', clean)
    # Remove port or path if included
    clean = clean.split('/')[0].split(':')[0].strip()
    # Strip syntactic trailing dot
    clean = clean.rstrip('.')
    if not clean:
        raise ValueError("Domain cannot be empty.")
    
    # IDNA Punycode conversion for strict canonical representation
    # This guarantees that 'bücher.example' and 'xn--bcher-kva.example' normalize to identical canonical forms
    try:
        punycode = clean.encode("idna").decode("ascii").lower()
        return punycode
    except Exception as exc:
        # Fallback to standard lowercase if IDNA encoder fails on non-standard labels
        return clean.lower()


def canonicalize_url(val: str) -> str:
    """
    Deterministically normalizes a URL indicator without destroying semantic path/query parameters.
    
    Transforms:
      - Defangs hxxp://, hxxps://, [.]
      - Lowercases scheme and netloc (with domain canonicalization)
      - Normalizes empty path to '/' if host-only, but PRESERVES exact path and query string
      - Preserves case in path and query parameters where case-sensitivity matters
    """
    clean = defang_text(val).strip()
    if not re.match(r'^[a-zA-Z]+:\/\/', clean):
        clean = "http://" + clean  # Assume http if scheme omitted
    
    parsed = urlparse(clean)
    scheme = parsed.scheme.lower()
    netloc = parsed.netloc.lower()

    # Canonicalize host within netloc (handling port if present)
    if ':' in netloc:
        host, port = netloc.split(':', 1)
        host_canon = canonicalize_domain(host)
        # Drop default ports
        if (scheme == "http" and port == "80") or (scheme == "https" and port == "443"):
            netloc = host_canon
        else:
            netloc = f"{host_canon}:{port}"
    else:
        netloc = canonicalize_domain(netloc)

    path = parsed.path or "/"
    # Do NOT strip or lowercase query or fragment as they constitute critical malicious payload markers
    canon_parsed = parsed._replace(scheme=scheme, netloc=netloc, path=path)
    return urlunparse(canon_parsed)


def canonicalize_hash(val: str, expected_type: IOCType = IOCType.SHA256) -> str:
    """
    Deterministically normalizes cryptographic hash strings.
    
    Transforms:
      - Strips whitespace
      - Lowercases hex string
      - Validates bit length (64 hex characters for SHA-256, 32 for MD5)
    """
    clean = val.strip().lower()
    if expected_type == IOCType.SHA256:
        if not re.match(r'^[0-9a-f]{64}$', clean):
            raise ValueError(f"Invalid SHA-256 hash length/format: {val}")
        return clean
    elif expected_type == IOCType.MD5:
        if not re.match(r'^[0-9a-f]{32}$', clean):
            raise ValueError(f"Invalid MD5 hash length/format: {val}")
        return clean
    return clean


def mask_sensitive_identifier(val: str, identifier_type: str = "phone") -> Tuple[str, str]:
    """
    Masks sensitive PII (Phone, Bank Account) for safe display while computing a deterministic SHA-256 digest.
    
    Returns:
      (masked_value, sha256_digest)
    """
    clean = re.sub(r'[\s\-\(\)\+]', '', val.strip())
    digest = hashlib.sha256(clean.encode("utf-8")).hexdigest()[:16]
    
    if identifier_type.lower() == "phone":
        if len(clean) >= 4:
            masked = f"XXXX-XXXX-{clean[-4:]}"
        else:
            masked = "XXXX-XXXX-XXXX"
    elif identifier_type.lower() in ["bank", "bank_account", "bankaccount"]:
        if len(clean) >= 4:
            masked = f"XXXX-XXXX-{clean[-4:]}"
        else:
            masked = "XXXX-XXXX-XXXX"
    else:
        masked = f"MASKED-{digest[:8]}"
        
    return masked, digest


def normalize_indicator(indicator_val: str, ioc_type: IOCType) -> str:
    """
    Dispatches indicator normalization based on declared IOCType.
    Raises ValueError on syntax violations.
    """
    if ioc_type == IOCType.IPV4:
        return canonicalize_ipv4(indicator_val)
    elif ioc_type == IOCType.IPV6:
        return canonicalize_ipv6(indicator_val)
    elif ioc_type == IOCType.DOMAIN:
        return canonicalize_domain(indicator_val)
    elif ioc_type == IOCType.URL:
        return canonicalize_url(indicator_val)
    elif ioc_type == IOCType.SHA256:
        return canonicalize_hash(indicator_val, IOCType.SHA256)
    elif ioc_type == IOCType.MD5:
        return canonicalize_hash(indicator_val, IOCType.MD5)
    elif ioc_type in (IOCType.PHONE, IOCType.BANK_ACCOUNT):
        masked, digest = mask_sensitive_identifier(indicator_val, ioc_type.value)
        return digest
    else:
        return indicator_val.strip().lower()
