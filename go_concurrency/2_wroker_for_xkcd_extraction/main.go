package main

import (
	"fmt"
	"io"
	"net/http"
	"time"
)

var conf config

func fetch(url string) (data []byte, err error) {

	// Make a get request
	response, err := http.Get(url)
	if err != nil {
		fmt.Printf("\033[38;5;9mError fetching data from url(%s): %s\033[0m", url, err.Error())
		return
	}

	// read response body
	defer response.Body.Close()

	data, err = io.ReadAll(response.Body)
	if err != nil {
		fmt.Printf("\033[38;5;9mError when reading response body: %s\033[0m", err.Error())
		return

	}

	fmt.Printf("\033[38;5;10m[COMPLETED FOR URL] %s\033[0m\n", url)

	return data, err
}

func init() {
	conf = NewConfig()
}

func main() {

	START_TIME := time.Now()

	jobs := make(chan int, conf.BufferSize)
	results := make(chan Result, conf.BufferSize)
	resultError := make(chan ResultsError, conf.BufferSize)
	completed := make(chan bool)

	fmt.Printf("\033[38;5;14m; Launching Workers := %d\033[0m\n", conf.NWorkers)
	for i := 1; i <= conf.NWorkers; i++ {
		go workers(i, jobs, results, resultError)
	}

	go consolidater(results, resultError, completed)

	launchJobs(jobs)
	close(jobs)

	fmt.Printf("Completed: %v\n", <-completed)
	fmt.Println("Time Taken: %v", time.Since(START_TIME))

}
