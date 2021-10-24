import socket
from threading import Thread
from os import path

WEBSITE_DIR = "website"
ERROR_403 = "403 Forbidden"
ERROR_404 = "404 Not Found"
DEFAULT_MIME_TYPE = "application/octet-stream"

ext_type_dict = {"html": "text/html", "js": "text/javascript; charset=UTF-8", "css": "text/css"}
image_types = ["png", "jpg", "jpeg"]


def get_http_line(sock):
    line = ""
    while line[-2:] != '\r\n':
        data = sock.recv(1).decode()
        line += data
    line = line.rstrip()
    return line


def get_http_req(sock):
    # recv until we see an empty line
    req = []
    line = get_http_line(sock)
    while line != '':
        req.append(line)
        line = get_http_line(sock)
    return req


def parse_http_req(http_req):
    """
    Return value is a dict:
    "method" = "GET"/"POST"/etc
    "path" = the path
    "protocol" = "HTTP/1.1", etc
    "headers" = a dict of the headers
    """
    first_line = http_req[0]
    first_line = first_line.split()
    method = first_line[0]
    http_path = first_line[1]
    protocol = first_line[2]
    req = {"method": method, "path": http_path, "protocol": protocol}
    headers = {}
    for i in range(1, len(http_req)):
        header = http_req[i].split(": ", 1)
        headers[header[0]] = header[1]
    req["headers"] = headers
    return req


def build_http_resp(resp_dict):
    """
    resp_dict format:
    "resp_code" = "200 OK", etc
    "headers" = dict of headers
    "body" = the response body
    """
    resp = "HTTP/1.1 "
    resp += f"{resp_dict['resp_code']}\r\n"
    for header in resp_dict["headers"]:
        resp += f"{header}: {resp_dict['headers'][header]}\r\n"
    resp += "\r\n"
    resp = resp.encode() + resp_dict["body"]
    return resp


def main():
    server.bind(("0.0.0.0", 8422))
    server.listen()
    while True:
        (client_socket, client_address) = server.accept()

        def serve(sock):
            print("serving")
            req = parse_http_req(get_http_req(sock))
            print(req)
            req_path = req["path"]
            if req_path == "/":
                req_path = "/index.html"
            web_file = path.join(WEBSITE_DIR, req_path.strip("/"))
            print(web_file)
            resp_code = "200 OK"
            mime_type = "text/plain"
            try:
                fd = open(web_file, "rb")
                resp_body = fd.read()
                fd.close()
                file_ext = req_path.rsplit(".", 1)[1]
                try:
                    mime_type = ext_type_dict[file_ext]
                except KeyError:
                    # it's an image?
                    try:
                        for img_type in image_types:
                            if img_type == file_ext:
                                mime_type = f"image/{img_type}"
                                break
                    except KeyError:
                        mime_type = DEFAULT_MIME_TYPE
            except PermissionError:
                resp_code = ERROR_403
                resp_body = resp_code.encode()
            except FileNotFoundError:
                resp_code = ERROR_404
                resp_body = resp_code.encode()

            resp = {"resp_code": resp_code, "headers": {"Content-Length": len(resp_body),
                                                        "Content-Type": mime_type,
                                                        "Server": "lol"}}
            print(resp)
            resp["body"] = resp_body
            resp_data = build_http_resp(resp)
            sock.send(resp_data)
            sock.close()

        thread = Thread(target=serve, args=(client_socket,))
        thread.start()


server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("got KeyboardInterrupt, closing server.. bye :)")
        server.close()
