package main

import (
	"fmt"
	"time"
)

func main() {
	now := time.Now()
	add := now.Add(128 * time.Hour)
	const FORMAT = "January, Monday 02-01-2006 03:04:05.000 PM"
	fmt.Printf("Now: %s\nAfter: %s\n",
		now.Format(FORMAT), add.Format(FORMAT))
	fmt.Println(add.Sub(now) > 24*time.Hour)

}
