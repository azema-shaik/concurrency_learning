package main

import (
	"fmt"
	"os"
	"strconv"
	"time"
)

type Result struct {
	jobID  int
	result float64
}

func worker(workerID int, jobs <-chan Job, results chan<- Result) {
	fmt.Printf("\033[38;5;13m[INFO]: Worker ID: %d launched.\n", workerID)
	for job := range jobs {
		fmt.Printf("\033[38;5;10m[PROCESSING WORKER]: WorkerID: %d, JobID: %d\n\033[0m", workerID, job.jobID)
		result := job.CostlyOperation()
		fmt.Printf("\033[38;5;14m[PROCESSED WORKER]: WorkerID: %d,JobID: %d, Result: %f\n\033[0m",
			workerID, job.jobID, result)

		results <- Result{jobID: job.jobID, result: result}
	}
}

func consolidate(Nloop int, results <-chan Result, complete chan<- bool) {
	file, _ := os.Create("check.log")
	defer file.Close()

	number := 0

	for i := 0; i < Nloop; i++ {
		number += 1
		result := <-results
		fmt.Printf("\033[38;5;10m[FETCHING RESULT] JobID: %d\n\033[0m", result.jobID)
		fmt.Printf("\033[38;5;14m[FETCHED RESULT] JobID: %d, Result: %f\n\033[0m", result.jobID, result.result)
		file.Write([]byte(
			fmt.Sprintf("ID: %d, JobID: %d, Result: %f\n", number, result.jobID, result.result),
		))

	}
	complete <- true
}

func main() {

	buffer_size, err := strconv.Atoi(os.Args[1])
	if err != nil {
		fmt.Println("Error: ", err)
		return
	}

	const NWorkers = 500
	NumberOfWork := 10_000_00

	jobs := make(chan Job, buffer_size)
	results := make(chan Result, buffer_size)
	completed := make(chan bool)

	timeNow := time.Now()

	for i := 1; i <= NWorkers; i++ {
		go worker(i, jobs, results)
	}
	go consolidate(NumberOfWork, results, completed)

	for i := 1; i <= NumberOfWork; i++ {
		jobs <- Job{jobID: i}

	}

	close(jobs)

	CompletedIn := time.Since(timeNow)

	fmt.Printf("COmpleted: %v totalTime: %v\n", <-completed, CompletedIn)

	file, _ := os.Create("duration.txt")
	file.Write([]byte(CompletedIn.String()))
	file.Close()

}
