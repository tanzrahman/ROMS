import ftplib
import os
from django.conf import settings
import datetime
import io
from io import FileIO
# from cryptography.fernet import Fernet

FILETYPE = {
            'avif': 'image/avif',
            'avi': 'video/x-msvideo',
            'csv': 'text/csv',
            'doc': 'application/msword',
            'docs': 'application/msword',
            'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'gif': 'image/gif',
            'jpeg' : 'image/jpeg',
            'jpg' : 'image/jpeg',
            'mid' : 'audio/midi',
            'midi' : 'audio/midi',
            'mp3' : 'audio/mpeg',
            'mp4' : 'video/mp4',
            'mpeg' : 'video/mpeg',
            'png' : 'image/png',
            'pdf' : 'application/pdf',
            'ppt' : 'application/vnd.ms-powerpoint',
            'pptx' : 'application/vnd.openxmlformats-officedocument.presentationml.presentation',
            'rar' : 'application/vnd.rar',
            'txt' : 'text/plain',
            'xls' : 'application/vnd.ms-excel',
            'xlsx' : 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            'zip' : 'application/zip',
            '7z' : 'application/x-7z-compressed'

          }

# def upload_to_ftp_enc(file_to_upload, filename, docType):
#     print(type(file_to_upload))
#
#     # key generation
#     #key = Fernet.generate_key()
#
#     # string the key in a file
#     #with open('encrypt_decrypt_key.key', 'wb') as filekey:
#         #filekey.write(key)
#     #print(key)
#
#     file = file_to_upload
#
#     session = ftplib.FTP(settings.FTP_SERVER,settings.FTP_USER,settings.FTP_PWD)
#
#     file_name = filename
#     date = datetime.datetime.today()
#     dir = date.strftime("%m%d%Y")
#     sub_dir = docType
#
#     #if the directory doesnt exists, create the directory
#     if dir not in session.nlst('/'.join(dir.split('/')[:-1])):
#         session.mkd(dir)
#     session.cwd(dir)
#
#     #for creating sub-directory under dir folder
#     if sub_dir not in session.nlst():
#         session.mkd(sub_dir)
#     session.cwd(sub_dir)
#
#     location = "/"+str(dir)+"/"+str(sub_dir)+"/"+file_name
#
#     cmd = 'STOR '+file_name
#     try:
#         session.storbinary(cmd, file)  # send the file
#
#         # file encryption
#         # ......................
#         # opening the key file
#         with open('encrypt_decrypt_key.key', 'rb') as file_key:
#             key = file_key.read()
#
#         # creating fernet object using the generated key
#         fernet = Fernet(key)
#
#         # encrypting the file
#         full_location = settings.FTP_BASE_DIR + location
#         with open(full_location, 'rb') as file:
#             original_file = file.read()
#
#         encrypted = fernet.encrypt(original_file)
#
#         # opening the file in write mode and writing the encrypted data
#         with open(full_location, 'wb') as encrypted_file:
#             encrypted_file.write(encrypted)
#
#         file.close()  # close file and FTP
#         session.quit()
#         return location
#
#     except Exception as E:
#         print(E)
#         return None
#
# def fetch_file_enc(request,file_url):
#     session = ftplib.FTP(settings.FTP_SERVER, settings.FTP_USER, settings.FTP_PWD)
#     tmp_file = "tmp.file"
#     full_location = settings.FTP_BASE_DIR+file_url
#     try:
#         with open(tmp_file,"wb") as f:
#             session.retrbinary('RETR %s' % full_location,f.write)
#     except Exception as e:
#         print("test")
#         print(e)
#
#     file = None
#     with open(tmp_file, 'rb') as f:
#         file = f.read()
#         f.close()
#     os.remove(tmp_file)
#
#     # decryption the requested file by opening the same key file
#     with open('encrypt_decrypt_key.key', 'rb') as file_key:
#         key = file_key.read()
#
#     fernet = Fernet(key)
#
#     # opening the encrypted file
#     with open(full_location, 'rb') as e_file:
#         encrypted_file = e_file.read()
#
#     # decrypting the file
#     decrypted_file = fernet.decrypt(encrypted_file)
#
#     return decrypted_file


def upload_to_ftp(file_to_upload, filename, docType=""):
    session = ftplib.FTP(
        settings.FTP_SERVER,
        settings.FTP_USER,
        settings.FTP_PWD
    )

    date = datetime.datetime.today()
    dir = date.strftime("%m%d%Y")

    session.cwd(settings.FTP_BASE_DIR)

    if dir not in session.nlst():
        session.mkd(dir)

    session.cwd(dir)

    try:
        # 🔥 rewind file before upload
        file_to_upload.seek(0)

        session.storbinary(f'STOR {filename}', file_to_upload)

        session.quit()

        return f"/{dir}/{filename}"

    except Exception as e:
        session.quit()
        raise e

    # file = file_to_upload
    #
    # session = ftplib.FTP(settings.FTP_SERVER,settings.FTP_USER,settings.FTP_PWD)
    #
    # file_name = filename
    # date = datetime.datetime.today()
    # dir = date.strftime("%m%d%Y")
    # session.cwd(settings.FTP_BASE_DIR)
    # #if the directory doesnt exists, create the directory
    # if dir not in session.nlst('/'.join(dir.split('/')[:-1])):
    #     session.mkd(dir)
    #
    # #GOTO base_dir -> date_dir
    # upload_dir = settings.FTP_BASE_DIR +"/"+ dir
    # session.cwd(upload_dir)
    #
    # # #for creating sub-directory under dir folder
    # # if sub_dir not in session.nlst():
    # #     session.mkd(sub_dir)
    # # session.cwd(sub_dir)
    #
    # location = "/"+str(dir)+"/"+file_name
    #
    # cmd = 'STOR '+file_name
    # try:
    #     session.storbinary(cmd, file)  # send the file
    #     file.close()  # close file and FTP
    #     session.quit()
    #     return location
    # except Exception as E:
    #     print("FTP_ERROR: "+E.__str__())
    #     return None

def fetch_file(request,file_url):
    session = ftplib.FTP(
        settings.FTP_SERVER,
        settings.FTP_USER,
        settings.FTP_PWD
    )

    buffer = io.BytesIO()
    full_location = settings.FTP_BASE_DIR + file_url

    session.retrbinary(f'RETR {full_location}', buffer.write)
    session.quit()

    buffer.seek(0)  # 🔥 REQUIRED
    return buffer.read()

    # session = ftplib.FTP(settings.FTP_SERVER, settings.FTP_USER, settings.FTP_PWD)
    # tmp_file = "tmp.file"
    # full_location = settings.FTP_BASE_DIR+file_url
    # try:
    #     with open(tmp_file,"wb") as f:
    #         session.retrbinary('RETR %s' % full_location,f.write)
    # except Exception as e:
    #     print(e)
    #
    # file = None
    # with open(tmp_file, 'rb') as f:
    #     file = f.read()
    #     f.close()
    # os.remove(tmp_file)
    # # Watermarking in every page of pdf file
    # # compatible with Python versions 2.6, 2.7,
    # # and 3.2 - 3.5. (pip3 install pypdf4)



    return file

def delete_file(file_url):
    session = ftplib.FTP(settings.FTP_SERVER, settings.FTP_USER, settings.FTP_PWD)
    full_location = settings.FTP_BASE_DIR + file_url
    try:
        session.delete(full_location)
    except Exception as e:
        print("FTP_ERROR: "+e.__str__())