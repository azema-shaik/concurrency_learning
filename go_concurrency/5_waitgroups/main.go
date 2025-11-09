package main

import (
	"fmt"
	"sync"
)

func print(i int, word string, wg *sync.WaitGroup) {
	defer wg.Done()
	fmt.Printf("%d, %s\n", i, word)
}

func main() {
	var wg sync.WaitGroup
	words := []string{
		"thranduil", "legolas", "eowyn", "galadriel", "mithrandier", "bilbo", "frodo", "aragon", "erwen",
	}
	for i, word := range words {
		wg.Add(1)
		go print(i, word, &wg)
	}

	wg.Wait()
}
