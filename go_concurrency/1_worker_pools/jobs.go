package main

import (
	"math"
	"time"
)

type Job struct {
	jobID int
}

func (j Job) CostlyOperation() float64 {
	time.Sleep(1 * time.Second)
	return math.Pow(float64(j.jobID), 2)
}
