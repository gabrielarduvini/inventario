<?php

use Illuminate\Support\Facades\Route;

Route::get('/', function () {
    return view('welcome');
});
use App\Http\Controllers\Api\ComputerController;

Route::post('/computers', [ComputerController::class, 'store']);