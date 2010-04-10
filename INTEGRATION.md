## HTTP Methods

* /send
  
  Accepts POST data with keys "message" and "number" and immediately
  dispatches messages to the modem
* [/status](/status) (Returns a multi-line status string)
* [/list](/list) (returns a list of received messages as JSON)

## Server Authentication

TODO

## Sending a Message

Python

    >>> params = urllib.urlencode({'message': 'Hello, world', 'number': 19737144557})
    >>> urllib.urlopen('http://127.0.0.1:8080/send', params).read()

PHP

    if (function_exists('curl_init')) {
      $request = curl_init();
      $headers[] = 'User-Agent: YourApp (+http://yourapp.com/)';
      curl_setopt($request, CURLOPT_URL, $endpoint);
      curl_setopt($request, CURLOPT_POST, TRUE);
      curl_setopt($request, CURLOPT_POSTFIELDS, $params);
      curl_setopt($request, CURLOPT_RETURNTRANSFER, TRUE);
      curl_setopt($request, CURLOPT_HTTPHEADER, $headers);
      curl_setopt($request, CURLOPT_HEADER, TRUE);
      $data = curl_exec($request);
      $header_size = curl_getinfo($request, CURLINFO_HEADER_SIZE);
      curl_close ($request); 
      return substr($data, $header_size);
    } 
