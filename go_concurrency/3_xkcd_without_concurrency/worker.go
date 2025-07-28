package main

import (
	"fmt"
	"os"
)

func fetchResults() {
	jsonlF, _ := os.Create("data/results.jsonl")
	loggerF, _ := os.Create("data/errorF.log")

	defer jsonlF.Close()
	defer loggerF.Close()

	for i := 1; i <= conf.NJobs; i++ {
		if response, err := fetch(fmt.Sprintf("https://xkcd.com/%d/info.0.json", i)); err != nil {
			responseErr := ResultsError{ID: i, Error: err.Error()}
			resp, _ := responseErr.Serialize()
			resp = append(resp, 10)
			loggerF.Write(resp)
		} else {
			result, _ := NewResult(response)
			result.ID = i
			resp, _ := result.Serialize()
			resp = append(resp, 10)
			jsonlF.Write(resp)
		}
		fmt.Sprintf("Fetched results from: %d\n", i)
	}

}
