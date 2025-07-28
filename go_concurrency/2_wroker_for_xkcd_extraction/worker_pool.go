package main

import (
	"fmt"
	"os"
)

func workers(id int, jobs <-chan int, results chan<- Result, resultErr chan<- ResultsError) {

	fmt.Printf("\033[38;5;3m[LAUNCHED WORKER] Worker ID: %d\033[0m\n", id)

	for job := range jobs {
		url := fmt.Sprintf("https://xkcd.com/%d/info.0.json", job)

		fmt.Printf("\033[38;5;5m[PROCESSING] Job: %d\033[0m\n", job)

		if data, err := fetch(url); err != nil {
			fmt.Printf("\033[38;5;5mError when fetching for id(%d): %s\033[0m\n", job, err.Error())
		} else {

			result, err := NewResult(data)

			if err != nil {
				resultErr <- ResultsError{ID: job, Error: err.Error()}
			}

			result.ID = job
			results <- result
		}

		fmt.Printf("\033[38;5;14m[PROCEED JOBS]Job: %d\033[0m\n", job)

	}
}

func consolidater(results <-chan Result, resultsErr <-chan ResultsError, completed chan<- bool) {
	jsonlF, _ := os.Create("data/results.jsonl")
	loggerF, _ := os.Create("data/errorF.log")

	defer jsonlF.Close()
	defer loggerF.Close()

	fmt.Printf("\033[38;5;3m[LAUNCHED CONSOLIDATOR]\033[0m\n")
	for i := 0; i <= conf.NJobs; i += 1 {

		select {
		case result := <-results:
			if data, err := result.Serialize(); err != nil {
				loggerF.WriteString(fmt.Sprintf("Loop ID: %d, JobID: %d, err: %s\n", i, result.ID, err.Error()))
			} else {
				data = append(data, 10)
				jsonlF.Write(data)
			}
		case resultErr := <-resultsErr:
			data, err := resultErr.Serialize()
			if err != nil {
				data = []byte(err.Error())
			}
			data = append(data, 10)
			loggerF.Write(data)
		}

	}

	completed <- true
}

func launchJobs(jobs chan<- int) {
	for i := 1; i <= conf.NJobs; i += 1 {
		jobs <- i
	}
	fmt.Println("\033[38;5;5m[INFO] Launched all JOBS!\033[0m")
}
