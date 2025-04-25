# v5.5
import hashlib
import random
from binascii import hexlify, unhexlify
import json

def derive_key(key, iv, phrase=None, N=None, salt=None):
    try:
        from Crypto.Protocol.KDF import scrypt
        from Crypto.Random import get_random_bytes
    except ImportError as e:
        raise ImportError("pycryptodome is required. Please run pip install pycryptodome") from e
    
    if not N:
        N = 262144
    else:
        try:
            N = int(N)
        except Exception:
            raise ValueError("Invalid N")
    if N > 2097152:
        raise ValueError("N is too large! Your device might be frozen!")
    
    # (2) 生成salt
    if not salt:
        salt = get_random_bytes(64)
    
    # 处理phrase
    if not phrase:
        phrases = ['Furina', 'Neuvillette', 'Venti', 'Nahida', 'Kinich', 'Kazuha']
        phrase = random.choice(phrases)
    if ':' in phrase:
        raise ValueError("phrase MUST NOT contain \":\"")
    
    parameter = f"{phrase}:{hexlify(salt).decode('ascii')}"
    
    # (3) 生成加密密钥
    key_input = f'MyEncryption/1.1 Fontaine/4.2 Iv/{hexlify(iv).decode("ascii")} user_parameter={parameter} user_key={key}'
    
    # 使用Scrypt进行密钥派生 (pycryptodome没有PBKDF2HMAC，使用Scrypt作为替代)
    # AES-256需要32字节密钥
    derived_key = scrypt(password=key_input.encode('utf-8'), salt=salt, key_len=32, N=N, r=8, p=1)
    
    return derived_key, parameter, N

def encrypt_data(message, key, phrase=None, N=None):
    try:
        from Crypto.Cipher import AES
        from Crypto.Protocol.KDF import scrypt
        from Crypto.Random import get_random_bytes
    except ImportError as e:
        raise ImportError("pycryptodome is required. Please run pip install pycryptodome") from e
    
    # (1) 生成随机IV (12 bytes for GCM)
    iv = get_random_bytes(12)
    
    # 派生密钥
    derived_key, parameter, N = derive_key(key, iv, phrase, N)
    
    # (4) 加密消息
    cipher = AES.new(derived_key, AES.MODE_GCM, nonce=iv)
    
    if isinstance(message, str):
        message = message.encode('utf-8')
    
    ciphertext, tag = cipher.encrypt_and_digest(message)
    
    # 组合IV + 密文 + 认证标签
    encrypted_message = iv + ciphertext + tag
    message_encrypted = hexlify(encrypted_message).decode('ascii')   
    return json.dumps({"data":message_encrypted,"parameter":parameter,"N":N,"v":5.5})

def decrypt_data(message_encrypted, key):
    try:
        from Crypto.Cipher import AES
        from Crypto.Protocol.KDF import scrypt
    except ImportError as e:
        raise ImportError("pycryptodome is required. Please run pip install pycryptodome") from e

    # 将十六进制字符串转换回字节
    try:
        jsoned = json.loads(message_encrypted)
        message_encrypted = jsoned.get("data")
        parameter = jsoned.get("parameter")
        N = int(jsoned.get("N"))
        encrypted_data = unhexlify(message_encrypted)
        phrase, salt_b64 = parameter.split(':')
        salt = unhexlify(salt_b64)
    except Exception as e:
        raise ValueError("The message or parameters are bad.") from e

    # 提取 IV (前12字节)、密文和认证标签(最后16字节)
    if len(encrypted_data) < 28:  # 12 (IV) + 16 (tag)
        raise ValueError("The message was too short.")

    iv = encrypted_data[:12]
    ciphertext = encrypted_data[12:-16]
    tag = encrypted_data[-16:]

    # (3) 重新生成加密密钥 (与加密过程相同)
    # 重新派生密钥
    derived_key, _, _ = derive_key(key, iv, phrase, N, salt)

    # 解密
    try:
        cipher = AES.new(derived_key, AES.MODE_GCM, nonce=iv)
        decrypted_data = cipher.decrypt_and_verify(ciphertext, tag)
    except BaseException as e:
        raise e

    # 尝试解码为UTF-8字符串，如果不是则返回字节
    try:
        return decrypted_data.decode('utf-8')
    except UnicodeDecodeError:
        return decrypted_data

# 新增文件处理函数
def encrypt_file(input_filename, output_filename, key, callback=None, phrase=None, N=None, chunk_size=32*1024*1024):
    try:
        from Crypto.Cipher import AES
        from Crypto.Random import get_random_bytes
    except ImportError as e:
        raise ImportError("pycryptodome is required. Please run pip install pycryptodome") from e

    try:
        with open(input_filename, 'rb') as fin, open(output_filename, 'wb') as fout:
            file_size = fin.seek(0, 2)  # 获取文件总大小
            fin.seek(0)  # 重置文件指针
            # 写入文件头标识和版本
            fout.write(b'MyEncryption/1.1')
            
            # 产生主密钥
            user_key = key
            # TODO: 主密钥的随机性非常重要！考虑让用户移动鼠标来收集随机性
            key = hexlify(get_random_bytes(64)).decode('ascii')
            ekey = encrypt_data(key, user_key)
            # 写入主密钥密文长度(4字节)和内容，填充到1024字节
            ekey_bytes = ekey.encode('utf-8')
            # 添加长度检查
            if len(ekey_bytes) > 1024:
                raise ValueError("(Internal Error) This should not happen. Contact the application developer.")
            # 写入主密钥密文长度(4字节)和内容，填充到1024字节
            fout.write(len(ekey_bytes).to_bytes(4, 'little'))  # 使用字节长度
            fout.write(ekey_bytes)  # 写入字节数据
            fout.write(b'\x00' * (1024 - len(ekey_bytes)))  # 使用字节长度计算填充
            
            # 生成初始IV用于派生密钥 (实际加密时每个分块会有自己的IV)
            iv_for_key = get_random_bytes(12)
            derived_key, parameter, N = derive_key(key, iv_for_key, phrase, N)
            
            # 准备头部JSON数据
            header_data = {
                "parameter": parameter,
                "N": N,
                "v": 5.5,
                "iv": hexlify(iv_for_key).decode('ascii')
            }
            header_json = json.dumps(header_data).encode('ascii')
            
            # 写入JSON长度和JSON数据
            fout.write(len(header_json).to_bytes(4, 'little'))
            fout.write(header_json)
            
            total_bytes = 0  # 用于统计总字节数
            
            # 分块加密处理
            nonce_counter = 1
            while True:
                chunk = fin.read(chunk_size)
                if not chunk:
                    break
                
                # 为每个分块生成新IV
                iv = nonce_counter.to_bytes(12, 'big')
                if nonce_counter >= 2**64:
                    raise ValueError("FATAL: IV Exception: nonce_counter exceeded the maximum value.")
                nonce_counter = nonce_counter + 1
                cipher = AES.new(derived_key, AES.MODE_GCM, nonce=iv)
                ciphertext, tag = cipher.encrypt_and_digest(chunk)
                
                # 写入分块信息: 原始数据长度(8字节) + IV(12字节) + 密文 + tag(16字节)
                chunk_len = len(chunk)
                fout.write(chunk_len.to_bytes(8, 'little'))
                fout.write(iv)
                fout.write(ciphertext)
                fout.write(tag)
                
                total_bytes += chunk_len  # 累加总字节数
                if callback:
                    callback(total_bytes, file_size)  # 调用回调函数报告进度
            
            # 写入结束标记和总字节数
            fout.write(b'\xFF\xFD\xF0\x10\x13\xD0\x12\x18')  # 8字节结束标记
            fout.write(total_bytes.to_bytes(8, 'little'))    # 8字节总长度
            fout.write(b'\x55\xAA')                         # 2字节结束符
        
        return True
    
    except Exception as e:
        raise e

def decrypt_file(input_filename, output_filename, key, callback=None):
    try:
        from Crypto.Cipher import AES
    except ImportError as e:
        raise ImportError("pycryptodome is required. Please run pip install pycryptodome") from e

    try:
        with open(input_filename, 'rb') as fin, open(output_filename, 'wb') as fout:
            file_size = fin.seek(0, 2)  # 获取文件总大小
            fin.seek(0)  # 重置文件指针
            
            # 验证文件头
            header = fin.read(16)
            if header != b'MyEncryption/1.1':
                raise ValueError("Invalid file format")
                
            # 读取主密钥密文长度(4字节)
            ekey_len = int.from_bytes(fin.read(4), 'little')
            # 读取主密钥密文
            ekey = fin.read(ekey_len).decode("utf-8")
            # 跳过填充部分(1024 - ekey_len)
            fin.read(1024 - ekey_len)
            # 使用用户提供的密钥解密主密钥
            key = decrypt_data(ekey, key)
            
            # 读取头部JSON
            json_len = int.from_bytes(fin.read(4), 'little')
            header_json = json.loads(fin.read(json_len).decode('ascii'))
            
            parameter = header_json["parameter"]
            N = int(header_json["N"])
            phrase, salt_b64 = parameter.split(':')
            salt = unhexlify(salt_b64)
            iv4key = unhexlify(header_json["iv"])

            # 对应加密时，需要提供一个iv，我们把iv取回来，重新生成密钥（所有数据块的密钥是相同的）
            derived_key, _, _ = derive_key(key, iv4key, phrase, N, salt)
            
            # 处理文件分块
            total = 0
            while True:
                # 读取分块信息
                chunk_len_bytes = fin.read(8)
                if not chunk_len_bytes or chunk_len_bytes == b'\xFF\xFD\xF0\x10\x13\xD0\x12\x18':
                    break
                chunk_len = int.from_bytes(chunk_len_bytes, 'little')
                iv = fin.read(12)
                ciphertext = fin.read(chunk_len)
                tag = fin.read(16)
                
                # 解密分块
                cipher = AES.new(derived_key, AES.MODE_GCM, nonce=iv)
                decrypted_chunk = cipher.decrypt_and_verify(ciphertext, tag)
                fout.write(decrypted_chunk)
                
                total = total + chunk_len
                if callback:
                    callback(total, file_size)  # 调用回调函数报告进度
            
            # 检查
            # 读取总字节数和结束符
            total_bytes = int.from_bytes(fin.read(8), 'little')
            end_marker = fin.read(2)
            
            # 验证总字节数是否匹配
            if total != total_bytes:
                raise ValueError("File corrupted: total bytes mismatch")
            
            # 验证结束标记是否正确
            if end_marker != b'\x55\xAA':
                raise ValueError("Invalid end marker")
        
        return True
    
    except Exception as e:
        raise e

def change_file_password(file, key, new_key):
    # TODO: 在更改密码前先备份主密钥，以防止意外断电导致文件损坏
    try:
        with open(file, 'r+b') as f:
            # 验证文件格式
            header = f.read(16)
            if header != b'MyEncryption/1.1':
                raise ValueError("Invalid file format")

            # 读取主密钥密文长度
            ekey_len = int.from_bytes(f.read(4), 'little')
            
            # 读取加密的主密钥
            ekey_ciphertext = f.read(ekey_len).decode('utf-8')

            # 用旧密码解密主密钥
            try:
                master_key = decrypt_data(ekey_ciphertext, key)
            except Exception as e:
                raise e

            # 用新密码重新加密主密钥
            new_ekey = encrypt_data(master_key, new_key)
            new_ekey_bytes = new_ekey.encode('utf-8')
            new_ekey_len = len(new_ekey_bytes)
            
            if new_ekey_len > 1024:
                raise ValueError("(Internal Error) This should not happen. Contact the application developer.")

            # 回写修改主密钥部分
            f.seek(16)  # 回到主密钥长度字段位置
            f.write(new_ekey_len.to_bytes(4, 'little'))
            f.write(new_ekey_bytes)
            f.write(b'\x00' * (1024 - new_ekey_len))  # 填充

            return True
    except Exception as e:
        raise RuntimeError(f"Unable to change password: {str(e)}") from e

def export_master_key(encrypted_file_path, current_key, export_key):
    try:
        from gc import collect
        with open(encrypted_file_path, 'rb') as f:
            # 验证文件头
            header = f.read(16)
            if header != b'MyEncryption/1.1':
                raise ValueError("Invalid file format")
            
            # 读取主密钥密文
            ekey_len = int.from_bytes(f.read(4), 'little')
            ekey_ciphertext = f.read(ekey_len).decode('utf-8')
            
            # 用current_key解密主密钥
            exported = encrypt_data(decrypt_data(ekey_ciphertext, current_key), export_key)
            collect()
            return exported
    
    except Exception as e:
        raise ValueError(f"Unable to export the key: {str(e)}")

if __name__=='__main__':
    print('This is a module. Always import it instead of running directly.')

#