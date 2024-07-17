package main

import (
	"bufio"
	"log"
	"net/http"
	"os"
	"time"

	"github.com/k0kubun/go-ansi"
	"github.com/schollz/progressbar/v3"
)

func main() {
	// Construct the HTTP client
	timeout, _ := time.ParseDuration("5s")
	client := &http.Client{
		Timeout: timeout,
	}

	// Open the file with domains
	pathname := "../domains.txt"
	file, err := os.Open(pathname)
	if err != nil {
		log.Fatal(err)
	}
	defer file.Close()

	bar := progressbar.NewOptions(2095,
		progressbar.OptionSetWriter(ansi.NewAnsiStdout()),
	)

	log.Printf("[INFO] Starting the checks…")

	// Try each domain
	scanner := bufio.NewScanner(file)
	for scanner.Scan() {
		url := scanner.Text()

		_, err := client.Get(url)
		if err == nil {
			// log.Printf("[PASS] %v", url)
		} else {
			log.Printf("[FAIL] ‹%v› with ‹%v›", url, err)
		}

		bar.Add(1)
	}
}
