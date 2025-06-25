package main

import (
	"encoding/json"
	"fmt"
	"os"
)

type Result struct {
	Month      int    `json:"month"`
	Year       int    `json:"year"`
	SafeTitle  string `json:"safe_title"`
	Transcript string `json:"transcript"`
	ImgUrl     string `json:"img"`
	Title      string `json:"title"`
	Day        string `json:"day"`
}

func NewResult(data string) (result Result) {

	//De-serialoze json
	if err := json.Unmarshal([]byte(data), result); err != nil {
		fmt.Printf("\033[38;5;9mError when deserializing json: %s\033[0m",
			err.Error())
		os.Exit(1)
	}

	return result
}
