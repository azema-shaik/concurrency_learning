package main

import (
	"io"
	"os"
	"strings"
	"sync"
	"testing"
)

func Test_print(t *testing.T) {

	r, w, _ := os.Pipe()
	os.Stdout = w

	var wg sync.WaitGroup
	wg.Add(1)

	go print(2, "bilbo", &wg)
	wg.Wait()

	w.Close()
	data, _ := io.ReadAll(r)
	res := string(data)

	if !strings.Contains(res, "bilbo") {
		t.Errorf("%s does not contain required string\n", res)
	}
}
