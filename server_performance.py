import socket
import time
import threading

def test_server_single_request(host, port, response_times, thread_id, local_port):
    expected_response_prefix = "Local time is: "

    try:
        # create a socket
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # bind to a different local port to simulate different users
        s.bind(('', local_port))

        # connect to the server
        start_time = time.time()
        s.connect((host, port))

        # send a simple HTTP request
        request = f"GET / HTTP/1.1\r\nHost: {host}:{port}\r\n\r\n"
        s.sendall(request.encode())

        # read the response
        response = s.recv(4096)
        end_time = time.time()

        # calculate the response time
        response_time = end_time - start_time
        response_times.append(response_time)

        # check if the response contains the expected prefix
        if expected_response_prefix.encode() not in response:
            print(f"thread {thread_id}: unexpected response: {response.decode(errors='ignore')}")
        else:
            print(f"thread {thread_id}: valid response received in {response_time:.4f} seconds")

        # close the socket
        s.close()

    except Exception as e:
        print(f"thread {thread_id}: request failed: {e}")

def test_server_performance_concurrent(host, port, num_requests):
    response_times = []
    threads = []

    for i in range(num_requests):
        # use different local ports to simulate different users
        local_port = 50000 + i
        thread = threading.Thread(target=test_server_single_request, args=(host, port, response_times, i, local_port))
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()

    if response_times:
        average_time = sum(response_times) / len(response_times)
        print(f"average response time: {average_time:.4f} seconds")
    else:
        print("no successful requests. your server must really suck.")

if __name__ == "__main__":
    # first test: single-threaded requests
    print("starting single-threaded test...")
    test_server_performance_concurrent("127.0.0.1", 8080, 1)
    
    # second test: two concurrent requests
    print("starting concurrent test with 2 threads...")
    test_server_performance_concurrent("127.0.0.1", 8080, 5)

