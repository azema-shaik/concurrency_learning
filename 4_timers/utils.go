package main

import "math/rand"

func getCPUusage() int {
	return rand.Intn(100) + 1
}
