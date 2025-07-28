package main

import (
	"encoding/json"
	"fmt"
	"os"
)

type Result struct {
	ID         int    `json:"id"`
	Month      string `json:"month"`
	Year       string `json:"year"`
	SafeTitle  string `json:"safe_title"`
	Transcript string `json:"transcript"`
	ImgUrl     string `json:"img"`
	Title      string `json:"title"`
	Day        string `json:"day"`
}

func NewResult(data []byte) (result Result, err error) {

	//De-serializing json
	if err = json.Unmarshal(data, &result); err != nil {
		fmt.Printf("\033[38;5;9mJson: %s\033[0m\n", string(data))
		fmt.Printf("\033[38;5;9mError when deserializing json: %s\033[0m",
			err.Error())
		return
	}

	return result, err
}

func (r Result) Serialize() ([]byte, error) {
	return json.Marshal(r)
}

type ResultsError struct {
	ID    int    `json:"id"`
	Error string `json:"error"`
}

func (re ResultsError) Serialize() ([]byte, error) {
	return json.Marshal(re)

}

type config struct {
	NWorkers   int `json:"n_workers"`
	NJobs      int `json:"n_jobs"`
	BufferSize int `json:"buffer_size"`
}

func NewConfig() (configuration config) {
	file, err := os.Open("config.json")
	if err != nil {
		fmt.Printf("\033[38;5;9mError when reading config file: %s\033[0m", err.Error())
		os.Exit(1)
	}

	defer file.Close()

	if err := json.NewDecoder(file).Decode(&configuration); err != nil {
		fmt.Printf("\033[38;5;9mError when deserializing json for config file: %s\033[0m", err.Error())
		os.Exit(1)
	}

	return configuration
}
