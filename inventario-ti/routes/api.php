<?php
use App\Http\Controllers\Api\ComputerController;

Route::post('/computers', [ComputerController::class, 'store']);
